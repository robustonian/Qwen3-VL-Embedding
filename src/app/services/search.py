import logging
import base64
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..config import settings
from ..database.chroma import chroma_manager
from ..database.sqlite import sqlite_manager

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.embedding_api_url = settings.EMBEDDING_API_URL

    def _build_file_type_filter(self, file_types: List[str]) -> Optional[Dict]:
        """Build ChromaDB where clause for file type filtering.

        Supported types:
        - 'text': file_type='text'
        - 'image': file_type='image' AND parent_document_id is empty (direct images only)
        - 'pdf': file_type='image' AND parent_document_id is not empty (PDF page images only)

        Note: Parent PDFs are not stored in ChromaDB (no embeddings), only in SQLite.
        ChromaDB contains: direct images, PDF page images, and text files.
        """
        if not file_types:
            return None

        conditions = []
        for ft in file_types:
            if ft == 'text':
                conditions.append({"file_type": {"$eq": "text"}})
            elif ft == 'image':
                # Direct images only (not PDF pages)
                # file_type="image" AND parent_document_id="" (empty means direct upload)
                conditions.append({
                    "$and": [
                        {"file_type": {"$eq": "image"}},
                        {"parent_document_id": {"$eq": ""}}
                    ]
                })
            elif ft == 'pdf':
                # PDF page images only
                # file_type="image" AND parent_document_id != "" (has parent = PDF page)
                conditions.append({
                    "$and": [
                        {"file_type": {"$eq": "image"}},
                        {"parent_document_id": {"$ne": ""}}
                    ]
                })

        if len(conditions) == 1:
            return conditions[0]
        return {"$or": conditions}

    async def _get_embedding(self, input_data: Any) -> List[float]:
        """Get embedding from the embedding API."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.embedding_api_url,
                json={
                    "input": input_data,
                    "model": "qwen3-vl-embedding"
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["data"][0]["embedding"]

    def _format_results(self, chroma_results: Dict) -> List[Dict[str, Any]]:
        """Format ChromaDB results into a cleaner structure."""
        results = []

        if not chroma_results["ids"] or not chroma_results["ids"][0]:
            return results

        ids = chroma_results["ids"][0]
        distances = chroma_results["distances"][0] if chroma_results.get("distances") else [0] * len(ids)
        metadatas = chroma_results["metadatas"][0] if chroma_results.get("metadatas") else [{}] * len(ids)

        for i, doc_id in enumerate(ids):
            # Convert distance to similarity score (cosine distance to similarity)
            # ChromaDB returns distance, lower is better
            # For cosine, distance = 1 - similarity, so similarity = 1 - distance
            distance = distances[i]
            similarity = 1 - distance

            results.append({
                "id": doc_id,
                "similarity": round(similarity * 100, 2),  # Convert to percentage
                "distance": distance,
                "metadata": metadatas[i]
            })

        return results

    async def search_by_text(
        self,
        query: str,
        limit: int = 20,
        file_types: List[str] = None,
        collection_id: str = None
    ) -> Dict[str, Any]:
        """Search documents by text query."""
        # Get embedding for query
        embedding = await self._get_embedding({
            "text": query,
            "instruction": "Retrieve relevant images or documents."
        })

        # Build filter
        where = {}
        file_type_filter = self._build_file_type_filter(file_types)
        if file_type_filter:
            where = file_type_filter
        if collection_id:
            if where:
                where = {"$and": [where, {"collection_id": collection_id}]}
            else:
                where["collection_id"] = collection_id

        # Search in ChromaDB
        chroma_results = chroma_manager.search(
            query_embedding=embedding,
            n_results=limit,
            where=where if where else None
        )

        results = self._format_results(chroma_results)

        # Log search history
        await sqlite_manager.add_search_history(
            query_type="text",
            query_text=query,
            result_count=len(results)
        )

        return {
            "query": query,
            "query_type": "text",
            "results": results,
            "total": len(results)
        }

    async def search_by_image(
        self,
        image_data: bytes,
        limit: int = 20,
        file_types: List[str] = None,
        collection_id: str = None
    ) -> Dict[str, Any]:
        """Search documents by image."""
        # Convert image to base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        image_input = f"data:image/jpeg;base64,{image_base64}"

        # Get embedding for image
        embedding = await self._get_embedding(image_input)

        # Build filter
        where = {}
        file_type_filter = self._build_file_type_filter(file_types)
        if file_type_filter:
            where = file_type_filter
        if collection_id:
            if where:
                where = {"$and": [where, {"collection_id": collection_id}]}
            else:
                where["collection_id"] = collection_id

        # Search in ChromaDB
        chroma_results = chroma_manager.search(
            query_embedding=embedding,
            n_results=limit,
            where=where if where else None
        )

        results = self._format_results(chroma_results)

        # Log search history
        await sqlite_manager.add_search_history(
            query_type="image",
            result_count=len(results)
        )

        return {
            "query_type": "image",
            "results": results,
            "total": len(results)
        }

    async def search_multimodal(
        self,
        text: str = None,
        image_data: bytes = None,
        limit: int = 20,
        file_types: List[str] = None,
        collection_id: str = None
    ) -> Dict[str, Any]:
        """Search with both text and image."""
        input_data = {}

        if text:
            input_data["text"] = text
            input_data["instruction"] = "Retrieve relevant images or documents."

        if image_data:
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            input_data["image"] = f"data:image/jpeg;base64,{image_base64}"

        if not input_data:
            raise ValueError("Either text or image must be provided")

        # Get embedding
        embedding = await self._get_embedding(input_data)

        # Build filter
        where = {}
        file_type_filter = self._build_file_type_filter(file_types)
        if file_type_filter:
            where = file_type_filter
        if collection_id:
            if where:
                where = {"$and": [where, {"collection_id": collection_id}]}
            else:
                where["collection_id"] = collection_id

        # Search in ChromaDB
        chroma_results = chroma_manager.search(
            query_embedding=embedding,
            n_results=limit,
            where=where if where else None
        )

        results = self._format_results(chroma_results)

        # Log search history
        await sqlite_manager.add_search_history(
            query_type="multimodal",
            query_text=text,
            result_count=len(results)
        )

        return {
            "query": text,
            "query_type": "multimodal",
            "results": results,
            "total": len(results)
        }

    async def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get recent search history."""
        return await sqlite_manager.get_recent_searches(limit)

search_service = SearchService()
