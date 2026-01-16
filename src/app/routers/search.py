import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel

from ..services.search import search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

class TextSearchRequest(BaseModel):
    query: str
    limit: int = 20
    file_types: Optional[List[str]] = None  # ['text', 'image', 'pdf']
    collection_id: Optional[str] = None

class SearchResultItem(BaseModel):
    id: str
    similarity: float
    distance: float
    metadata: dict

class SearchResponse(BaseModel):
    query: Optional[str] = None
    query_type: str
    results: List[SearchResultItem]
    total: int

class RecentSearchItem(BaseModel):
    id: int
    query_type: str
    query_text: Optional[str]
    result_count: int
    created_at: str

@router.post("/text", response_model=SearchResponse)
async def search_by_text(request: TextSearchRequest):
    """Search documents by text query."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    return await search_service.search_by_text(
        query=request.query,
        limit=request.limit,
        file_types=request.file_types,
        collection_id=request.collection_id
    )

@router.post("/image", response_model=SearchResponse)
async def search_by_image(
    image: UploadFile = File(...),
    limit: int = Form(20),
    file_types: Optional[str] = Form(None),  # JSON string array, e.g. '["text","image","pdf"]'
    collection_id: Optional[str] = Form(None)
):
    """Search documents by image."""
    # Validate image type
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_data = await image.read()

    # Parse file_types from JSON string if provided
    parsed_file_types = None
    if file_types:
        import json
        try:
            parsed_file_types = json.loads(file_types)
        except json.JSONDecodeError:
            # Fallback: treat as single value
            parsed_file_types = [file_types]

    return await search_service.search_by_image(
        image_data=image_data,
        limit=limit,
        file_types=parsed_file_types,
        collection_id=collection_id
    )

@router.post("/multimodal", response_model=SearchResponse)
async def search_multimodal(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    limit: int = Form(20),
    file_types: Optional[str] = Form(None),  # JSON string array
    collection_id: Optional[str] = Form(None)
):
    """Search with both text and image."""
    if not text and not image:
        raise HTTPException(status_code=400, detail="Either text or image must be provided")

    image_data = None
    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        image_data = await image.read()

    # Parse file_types from JSON string if provided
    parsed_file_types = None
    if file_types:
        import json
        try:
            parsed_file_types = json.loads(file_types)
        except json.JSONDecodeError:
            parsed_file_types = [file_types]

    return await search_service.search_multimodal(
        text=text,
        image_data=image_data,
        limit=limit,
        file_types=parsed_file_types,
        collection_id=collection_id
    )

@router.get("/history", response_model=List[RecentSearchItem])
async def get_search_history(limit: int = Query(10, ge=1, le=50)):
    """Get recent search history."""
    return await search_service.get_recent_searches(limit)
