import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database.sqlite import sqlite_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collections", tags=["collections"])

class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CollectionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str
    file_count: int = 0

class AddDocumentsRequest(BaseModel):
    document_ids: List[str]

@router.post("", response_model=CollectionResponse)
async def create_collection(request: CollectionCreate):
    """Create a new collection."""
    # Check if name already exists
    existing = await sqlite_manager.get_collection_by_name(request.name)
    if existing:
        raise HTTPException(status_code=400, detail="Collection name already exists")

    collection_id = str(uuid.uuid4())
    collection = await sqlite_manager.create_collection(
        collection_id=collection_id,
        name=request.name,
        description=request.description
    )

    return {**collection, "file_count": 0}

@router.get("", response_model=List[CollectionResponse])
async def list_collections():
    """List all collections."""
    return await sqlite_manager.get_collections()

@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(collection_id: str):
    """Get a single collection by ID."""
    collection = await sqlite_manager.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Get file count
    file_count = await sqlite_manager.count_files(collection_id=collection_id)
    return {**collection, "file_count": file_count}

@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(collection_id: str, request: CollectionUpdate):
    """Update a collection."""
    collection = await sqlite_manager.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    update_data = {}
    if request.name is not None:
        # Check if new name already exists
        existing = await sqlite_manager.get_collection_by_name(request.name)
        if existing and existing["id"] != collection_id:
            raise HTTPException(status_code=400, detail="Collection name already exists")
        update_data["name"] = request.name

    if request.description is not None:
        update_data["description"] = request.description

    if update_data:
        collection = await sqlite_manager.update_collection(collection_id, **update_data)

    file_count = await sqlite_manager.count_files(collection_id=collection_id)
    return {**collection, "file_count": file_count}

@router.delete("/{collection_id}")
async def delete_collection(collection_id: str):
    """Delete a collection (files are moved to uncategorized)."""
    collection = await sqlite_manager.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Remove collection_id from all files in this collection
    files = await sqlite_manager.get_files(collection_id=collection_id, limit=10000)
    for file in files:
        await sqlite_manager.update_file(file["id"], collection_id=None)

    await sqlite_manager.delete_collection(collection_id)

    return {"success": True, "id": collection_id}

@router.post("/{collection_id}/documents")
async def add_documents_to_collection(collection_id: str, request: AddDocumentsRequest):
    """Add documents to a collection."""
    collection = await sqlite_manager.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    updated = 0
    for doc_id in request.document_ids:
        doc = await sqlite_manager.get_file(doc_id)
        if doc:
            await sqlite_manager.update_file(doc_id, collection_id=collection_id)
            updated += 1

    return {"success": True, "updated": updated}

@router.delete("/{collection_id}/documents")
async def remove_documents_from_collection(collection_id: str, request: AddDocumentsRequest):
    """Remove documents from a collection."""
    collection = await sqlite_manager.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    updated = 0
    for doc_id in request.document_ids:
        doc = await sqlite_manager.get_file(doc_id)
        if doc and doc.get("collection_id") == collection_id:
            await sqlite_manager.update_file(doc_id, collection_id=None)
            updated += 1

    return {"success": True, "updated": updated}
