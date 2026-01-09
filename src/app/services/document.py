import logging
import hashlib
import uuid
import aiofiles
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..config import settings
from ..database.chroma import chroma_manager
from ..database.sqlite import sqlite_manager
from .thumbnail import thumbnail_service

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        self.embedding_api_url = settings.EMBEDDING_API_URL

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

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _determine_file_type(self, mime_type: str) -> str:
        """Determine file type from MIME type."""
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type == "application/pdf":
            return "document"
        elif mime_type.startswith("text/"):
            return "text"
        else:
            return "other"

    def _get_storage_path(self, file_id: str, file_type: str, original_name: str) -> Path:
        """Generate organized storage path."""
        if file_type == "image":
            base_dir = settings.IMAGES_DIR
        else:
            base_dir = settings.DOCUMENTS_DIR

        # Use first 2 chars of ID for directory sharding
        shard = file_id[:2]
        shard_dir = base_dir / shard
        shard_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(original_name).suffix
        return shard_dir / f"{file_id}{ext}"

    async def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        mime_type: str,
        collection_id: str = None
    ) -> Dict[str, Any]:
        """Upload and process a single file."""
        file_id = str(uuid.uuid4())
        file_type = self._determine_file_type(mime_type)

        # Determine storage path
        storage_path = self._get_storage_path(file_id, file_type, file_name)

        # Save file
        async with aiofiles.open(storage_path, "wb") as f:
            await f.write(file_content)

        file_size = len(file_content)
        content_hash = hashlib.sha256(file_content).hexdigest()

        # Generate thumbnail for images
        thumbnail_path = None
        if file_type == "image":
            try:
                thumb_path = thumbnail_service.generate(storage_path, f"{file_id}_thumb.webp")
                thumbnail_path = str(thumb_path)
            except Exception as e:
                logger.warning(f"Failed to generate thumbnail: {e}")

        # Get embedding
        try:
            if file_type == "image":
                embedding = await self._get_embedding(str(storage_path))
            else:
                # For text/documents, read content
                async with aiofiles.open(storage_path, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = await f.read()
                embedding = await self._get_embedding(text_content[:8000])  # Limit text length
        except Exception as e:
            logger.error(f"Failed to get embedding for {file_name}: {e}")
            # Clean up on failure
            storage_path.unlink(missing_ok=True)
            if thumbnail_path:
                Path(thumbnail_path).unlink(missing_ok=True)
            raise

        # Store in ChromaDB
        metadata = {
            "file_name": file_name,
            "file_path": str(storage_path),
            "file_type": file_type,
            "mime_type": mime_type,
            "file_size": file_size,
            "created_at": datetime.utcnow().isoformat(),
            "thumbnail_path": thumbnail_path or "",
            "collection_id": collection_id or ""
        }
        chroma_manager.add_document(file_id, embedding, metadata)

        # Store in SQLite
        await sqlite_manager.create_file(
            file_id=file_id,
            file_name=file_name,
            file_path=str(storage_path),
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            content_hash=content_hash,
            thumbnail_path=thumbnail_path,
            collection_id=collection_id
        )

        logger.info(f"Uploaded file: {file_name} ({file_id})")

        return {
            "id": file_id,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "thumbnail_path": thumbnail_path,
            "collection_id": collection_id
        }

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        return await sqlite_manager.get_file(doc_id)

    async def get_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        file_type: str = None,
        collection_id: str = None
    ) -> Dict[str, Any]:
        """Get documents with pagination."""
        files = await sqlite_manager.get_files(
            limit=limit,
            offset=offset,
            file_type=file_type,
            collection_id=collection_id
        )
        total = await sqlite_manager.count_files(
            file_type=file_type,
            collection_id=collection_id
        )

        return {
            "items": files,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document and all associated data."""
        doc = await sqlite_manager.get_file(doc_id)
        if not doc:
            return False

        # Delete file from storage
        file_path = Path(doc["file_path"])
        if file_path.exists():
            file_path.unlink()

        # Delete thumbnail
        if doc.get("thumbnail_path"):
            thumb_path = Path(doc["thumbnail_path"])
            if thumb_path.exists():
                thumb_path.unlink()

        # Delete from ChromaDB
        chroma_manager.delete_document(doc_id)

        # Delete from SQLite
        await sqlite_manager.delete_file(doc_id)

        logger.info(f"Deleted document: {doc_id}")
        return True

    async def delete_documents(self, doc_ids: List[str]) -> int:
        """Delete multiple documents."""
        deleted = 0
        for doc_id in doc_ids:
            if await self.delete_document(doc_id):
                deleted += 1
        return deleted

    async def get_stats(self) -> Dict[str, Any]:
        """Get document statistics."""
        stats = await sqlite_manager.get_stats()
        stats["chroma_count"] = chroma_manager.count()
        return stats

document_service = DocumentService()
