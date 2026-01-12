import logging
import json
import asyncio
import uuid
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel

from ..services.document import document_service
from ..services.progress import progress_manager
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

class DocumentResponse(BaseModel):
    id: str
    file_name: str
    file_type: str
    file_size: int
    thumbnail_path: Optional[str] = None
    collection_id: Optional[str] = None

class DocumentListResponse(BaseModel):
    items: List[dict]
    total: int
    limit: int
    offset: int

class DeleteRequest(BaseModel):
    ids: List[str]

class StatsResponse(BaseModel):
    total_files: int
    total_collections: int
    files_by_type: dict
    chroma_count: int

@router.post("/upload", response_model=List[DocumentResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    collection_id: Optional[str] = Form(None)
):
    """Upload one or more files."""
    results = []
    errors = []

    for file in files:
        # Validate file type
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES and \
           file.content_type not in settings.ALLOWED_DOCUMENT_TYPES:
            errors.append(f"Unsupported file type: {file.filename} ({file.content_type})")
            continue

        # Read file content
        content = await file.read()

        # Validate file size
        if len(content) > settings.MAX_FILE_SIZE:
            errors.append(f"File too large: {file.filename}")
            continue

        try:
            result = await document_service.upload_file(
                file_content=content,
                file_name=file.filename,
                mime_type=file.content_type,
                collection_id=collection_id
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {e}")
            errors.append(f"Failed to process: {file.filename}")

    if errors and not results:
        raise HTTPException(status_code=400, detail=errors)

    return results


@router.post("/upload/stream")
async def upload_documents_stream(
    files: List[UploadFile] = File(...),
    collection_id: Optional[str] = Form(None)
):
    """Upload files with streaming progress (for PDFs with multiple pages).

    Returns newline-delimited JSON (NDJSON) with progress updates.
    Each line is a JSON object with type: "progress" | "complete" | "error"
    """
    async def generate():
        results = []
        errors = []

        for file_index, file in enumerate(files):
            # Validate file type
            if file.content_type not in settings.ALLOWED_IMAGE_TYPES and \
               file.content_type not in settings.ALLOWED_DOCUMENT_TYPES:
                errors.append(f"Unsupported file type: {file.filename} ({file.content_type})")
                yield json.dumps({
                    "type": "error",
                    "message": f"Unsupported file type: {file.filename}"
                }) + "\n"
                continue

            # Read file content
            content = await file.read()

            # Validate file size
            if len(content) > settings.MAX_FILE_SIZE:
                errors.append(f"File too large: {file.filename}")
                yield json.dumps({
                    "type": "error",
                    "message": f"File too large: {file.filename}"
                }) + "\n"
                continue

            try:
                # Create task for progress tracking
                task_id = str(uuid.uuid4())
                progress_manager.create_task(task_id, file.filename)

                # Send initial progress
                yield json.dumps({
                    "type": "progress",
                    "file_name": file.filename,
                    "file_index": file_index,
                    "total_files": len(files),
                    "status": "uploading",
                    "current_page": 0,
                    "total_pages": 0,
                    "message": f"ファイルを処理中: {file.filename}"
                }) + "\n"

                # Start processing with progress callback
                async def progress_callback(current_page: int, total_pages: int, message: str):
                    await progress_manager.update_progress(
                        task_id,
                        current_page=current_page,
                        total_pages=total_pages,
                        status="processing",
                        message=message
                    )

                # Subscribe to progress updates
                queue = progress_manager.subscribe(task_id)

                # Start upload in background
                upload_task = asyncio.create_task(
                    document_service.upload_file(
                        file_content=content,
                        file_name=file.filename,
                        mime_type=file.content_type,
                        collection_id=collection_id,
                        task_id=task_id
                    )
                )

                # Stream progress updates
                while not upload_task.done():
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=0.5)
                        yield json.dumps({
                            "type": "progress",
                            "file_name": file.filename,
                            "file_index": file_index,
                            "total_files": len(files),
                            "status": event.get("status", "processing"),
                            "current_page": event.get("current_page", 0),
                            "total_pages": event.get("total_pages", 0),
                            "message": event.get("message", "")
                        }) + "\n"
                    except asyncio.TimeoutError:
                        continue

                # Get result
                result = await upload_task
                results.append(result)

                # Cleanup
                progress_manager.unsubscribe(task_id, queue)
                progress_manager.cleanup_task(task_id)

                yield json.dumps({
                    "type": "file_complete",
                    "file_name": file.filename,
                    "file_index": file_index,
                    "total_files": len(files),
                    "result": result
                }) + "\n"

            except Exception as e:
                logger.error(f"Failed to upload {file.filename}: {e}")
                errors.append(f"Failed to process: {file.filename}")
                yield json.dumps({
                    "type": "error",
                    "file_name": file.filename,
                    "message": str(e)
                }) + "\n"

        # Final complete message
        yield json.dumps({
            "type": "complete",
            "results": results,
            "errors": errors
        }) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no"}  # Disable nginx buffering
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    file_type: Optional[str] = None,  # Single type (backward compatibility)
    file_types: Optional[List[str]] = Query(None),  # Multiple types
    collection_id: Optional[str] = None
):
    """List documents with pagination."""
    # file_types takes precedence over file_type
    types_to_filter = file_types if file_types else ([file_type] if file_type else None)
    return await document_service.get_documents(
        limit=limit,
        offset=offset,
        file_types=types_to_filter,
        collection_id=collection_id
    )

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get document statistics."""
    return await document_service.get_stats()

@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """Get a single document by ID."""
    doc = await document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/{doc_id}/content")
async def get_document_content(doc_id: str):
    """Get text content of a document."""
    doc = await document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(doc["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Only allow text files
    if doc["file_type"] not in ["text", "document"]:
        raise HTTPException(status_code=400, detail="Content only available for text/document files")

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {"content": content, "file_name": doc["file_name"]}
    except Exception as e:
        logger.error(f"Failed to read file content: {e}")
        raise HTTPException(status_code=500, detail="Failed to read file")

@router.get("/{doc_id}/parent")
async def get_parent_document(doc_id: str):
    """Get the parent document for a page image (e.g., original PDF for extracted pages)."""
    doc = await document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    parent_id = doc.get("parent_document_id")
    if not parent_id:
        return {"parent": None}

    parent = await document_service.get_document(parent_id)
    return {"parent": parent}

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a single document."""
    success = await document_service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True, "id": doc_id}

@router.post("/batch-delete")
async def batch_delete_documents(request: DeleteRequest):
    """Delete multiple documents."""
    deleted = await document_service.delete_documents(request.ids)
    return {"success": True, "deleted": deleted}

@router.post("/migrate-chroma")
async def migrate_chroma_metadata():
    """Migrate ChromaDB metadata to add missing fields.

    This endpoint adds the 'parent_document_id' field to existing ChromaDB
    records that don't have it. This is needed because older records may be
    missing this field, which causes type filtering to fail.

    Run this once after upgrading to fix filtering for existing data.
    """
    from ..database.chroma import chroma_manager
    updated = chroma_manager.migrate_add_parent_document_id()
    return {"success": True, "message": f"Migrated {updated} records", "updated_count": updated}
