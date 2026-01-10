import logging
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..services.document import document_service
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

@router.get("", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    file_type: Optional[str] = None,
    collection_id: Optional[str] = None
):
    """List documents with pagination."""
    return await document_service.get_documents(
        limit=limit,
        offset=offset,
        file_type=file_type,
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
