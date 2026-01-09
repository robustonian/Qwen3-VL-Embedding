from .documents import router as documents_router
from .search import router as search_router
from .collections import router as collections_router

__all__ = ["documents_router", "search_router", "collections_router"]
