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
from .pdf import pdf_service
from .progress import progress_manager

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
        collection_id: str = None,
        task_id: str = None
    ) -> Dict[str, Any]:
        """Upload and process a single file."""
        file_size = len(file_content)
        content_hash = hashlib.sha256(file_content).hexdigest()

        # Check for duplicate by content hash
        existing_file = await sqlite_manager.get_file_by_hash(content_hash)
        if existing_file:
            logger.info(f"Skipping duplicate file: {file_name} (matches {existing_file['id']})")
            return {
                "id": existing_file["id"],
                "file_name": existing_file["file_name"],
                "file_type": existing_file["file_type"],
                "file_size": existing_file["file_size"],
                "thumbnail_path": existing_file.get("thumbnail_path"),
                "collection_id": existing_file.get("collection_id"),
                "duplicate": True
            }

        file_id = str(uuid.uuid4())
        file_type = self._determine_file_type(mime_type)

        # Handle PDF specially - extract pages as images
        if mime_type == "application/pdf":
            return await self._process_pdf(
                file_content=file_content,
                file_name=file_name,
                file_id=file_id,
                content_hash=content_hash,
                collection_id=collection_id,
                task_id=task_id
            )

        # Determine storage path
        storage_path = self._get_storage_path(file_id, file_type, file_name)

        # Save file
        async with aiofiles.open(storage_path, "wb") as f:
            await f.write(file_content)

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
            "collection_id": collection_id or "",
            "parent_document_id": "",
            "page_number": 0
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

    async def _process_pdf(
        self,
        file_content: bytes,
        file_name: str,
        file_id: str,
        content_hash: str,
        collection_id: str = None,
        task_id: str = None
    ) -> Dict[str, Any]:
        """Process PDF: save original and extract pages as images."""
        file_size = len(file_content)

        # Save original PDF
        pdf_storage_path = self._get_storage_path(file_id, "document", file_name)
        async with aiofiles.open(pdf_storage_path, "wb") as f:
            await f.write(file_content)

        # Generate thumbnail from first page for the parent PDF
        parent_thumbnail_path = None
        try:
            base_name = Path(file_name).stem
            temp_pages = pdf_service.extract_pages_as_images(
                pdf_storage_path,
                settings.THUMBNAILS_DIR,
                f"{file_id}_temp"
            )
            if temp_pages:
                first_page_path, _ = temp_pages[0]
                parent_thumbnail_path = str(thumbnail_service.generate(
                    first_page_path, f"{file_id}_thumb.webp"
                ))
                # Clean up temp first page (we'll re-extract all pages properly)
                for temp_path, _ in temp_pages:
                    temp_path.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to generate PDF thumbnail: {e}")

        # Store parent PDF in SQLite (no embedding for parent)
        await sqlite_manager.create_file(
            file_id=file_id,
            file_name=file_name,
            file_path=str(pdf_storage_path),
            file_type="document",
            mime_type="application/pdf",
            file_size=file_size,
            content_hash=content_hash,
            thumbnail_path=parent_thumbnail_path,
            collection_id=collection_id,
            parent_document_id=None,
            page_number=None
        )

        # Extract pages as images
        base_name = Path(file_name).stem
        output_dir = settings.IMAGES_DIR / file_id[:2]

        pages = pdf_service.extract_pages_as_images(
            pdf_storage_path,
            output_dir,
            base_name
        )

        # Report total pages for progress tracking
        if task_id:
            await progress_manager.update_progress(
                task_id,
                total_pages=len(pages),
                status="processing",
                message=f"PDF解析完了: {len(pages)}ページ"
            )

        page_results = []
        for image_path, page_num in pages:
            # Report progress for each page
            if task_id:
                await progress_manager.update_progress(
                    task_id,
                    current_page=page_num,
                    total_pages=len(pages),
                    status="processing",
                    message=f"ページ {page_num}/{len(pages)} 処理中..."
                )
            page_id = str(uuid.uuid4())
            page_name = f"{base_name}_page{page_num}.png"

            # Generate thumbnail for page
            thumbnail_path = None
            try:
                thumb = thumbnail_service.generate(image_path, f"{page_id}_thumb.webp")
                thumbnail_path = str(thumb)
            except Exception as e:
                logger.warning(f"Failed to generate thumbnail for page {page_num}: {e}")

            # Get embedding for the page image
            try:
                embedding = await self._get_embedding(str(image_path))
            except Exception as e:
                logger.error(f"Failed to get embedding for page {page_num}: {e}")
                continue

            # Calculate hash for page image
            page_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()
            page_size = image_path.stat().st_size
            created_at = datetime.utcnow().isoformat()

            # ChromaDB metadata includes parent reference
            metadata = {
                "file_name": page_name,
                "file_path": str(image_path),
                "file_type": "image",
                "mime_type": "image/png",
                "file_size": page_size,
                "created_at": created_at,
                "thumbnail_path": thumbnail_path or "",
                "collection_id": collection_id or "",
                "parent_document_id": file_id,
                "page_number": page_num
            }
            chroma_manager.add_document(page_id, embedding, metadata)

            # SQLite storage
            await sqlite_manager.create_file(
                file_id=page_id,
                file_name=page_name,
                file_path=str(image_path),
                file_type="image",
                mime_type="image/png",
                file_size=page_size,
                content_hash=page_hash,
                thumbnail_path=thumbnail_path,
                collection_id=collection_id,
                parent_document_id=file_id,
                page_number=page_num
            )

            page_results.append({
                "id": page_id,
                "file_name": page_name,
                "page_number": page_num,
                "thumbnail_path": thumbnail_path
            })

        logger.info(f"Processed PDF {file_name}: {len(page_results)} pages")

        return {
            "id": file_id,
            "file_name": file_name,
            "file_type": "document",
            "file_size": file_size,
            "thumbnail_path": parent_thumbnail_path,
            "collection_id": collection_id,
            "pages": page_results
        }

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        return await sqlite_manager.get_file(doc_id)

    async def get_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        file_types: List[str] = None,
        collection_id: str = None
    ) -> Dict[str, Any]:
        """Get documents with pagination."""
        files = await sqlite_manager.get_files(
            limit=limit,
            offset=offset,
            file_types=file_types,
            collection_id=collection_id
        )
        total = await sqlite_manager.count_files(
            file_types=file_types,
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
