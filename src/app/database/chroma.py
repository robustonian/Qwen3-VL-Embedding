import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..config import settings

logger = logging.getLogger(__name__)

class ChromaManager:
    _instance = None
    _client = None
    _collection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize()

    def _initialize(self):
        """Initialize ChromaDB client and collection."""
        logger.info(f"Initializing ChromaDB at {settings.CHROMA_DIR}")

        self._client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DIR),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        self._collection = self._client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(f"ChromaDB collection '{settings.CHROMA_COLLECTION_NAME}' ready with {self._collection.count()} documents")

    @property
    def collection(self):
        return self._collection

    def add_document(
        self,
        doc_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """Add a document with its embedding and metadata."""
        self._collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[metadata]
        )
        logger.debug(f"Added document {doc_id} to ChromaDB")

    def add_documents(
        self,
        doc_ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add multiple documents with their embeddings and metadata."""
        self._collection.add(
            ids=doc_ids,
            embeddings=embeddings,
            metadatas=metadatas
        )
        logger.debug(f"Added {len(doc_ids)} documents to ChromaDB")

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar documents."""
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["metadatas", "distances"]
        )
        return results

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        results = self._collection.get(
            ids=[doc_id],
            include=["metadatas", "embeddings"]
        )
        if results["ids"]:
            return {
                "id": results["ids"][0],
                "metadata": results["metadatas"][0] if results["metadatas"] else {},
                "embedding": results["embeddings"][0] if results["embeddings"] else None
            }
        return None

    def delete_document(self, doc_id: str) -> None:
        """Delete a document by ID."""
        self._collection.delete(ids=[doc_id])
        logger.debug(f"Deleted document {doc_id} from ChromaDB")

    def delete_documents(self, doc_ids: List[str]) -> None:
        """Delete multiple documents by IDs."""
        self._collection.delete(ids=doc_ids)
        logger.debug(f"Deleted {len(doc_ids)} documents from ChromaDB")

    def update_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> None:
        """Update metadata for a document."""
        self._collection.update(
            ids=[doc_id],
            metadatas=[metadata]
        )
        logger.debug(f"Updated metadata for document {doc_id}")

    def count(self) -> int:
        """Get total document count."""
        return self._collection.count()

    def get_all_ids(self) -> List[str]:
        """Get all document IDs."""
        results = self._collection.get()
        return results["ids"]

    def reset(self) -> None:
        """Reset the collection (delete all documents)."""
        self._client.delete_collection(settings.CHROMA_COLLECTION_NAME)
        self._collection = self._client.create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("ChromaDB collection reset")

    def migrate_add_parent_document_id(self) -> int:
        """Add parent_document_id field to existing records that don't have it.

        This migration is needed because older records may not have this field,
        which causes filtering to fail (ChromaDB $eq/$ne only work when field exists).

        Returns:
            Number of records updated.
        """
        # Get all documents with their metadata
        all_docs = self._collection.get(include=["metadatas"])

        if not all_docs["ids"]:
            logger.info("No documents to migrate")
            return 0

        updated_count = 0
        for i, doc_id in enumerate(all_docs["ids"]):
            metadata = all_docs["metadatas"][i] if all_docs["metadatas"] else {}

            # Check if parent_document_id field is missing
            if "parent_document_id" not in metadata:
                # Add the field with empty string (default for direct uploads)
                metadata["parent_document_id"] = ""
                # Also ensure page_number exists
                if "page_number" not in metadata:
                    metadata["page_number"] = 0

                self._collection.update(
                    ids=[doc_id],
                    metadatas=[metadata]
                )
                updated_count += 1

        logger.info(f"Migrated {updated_count} ChromaDB records with parent_document_id field")
        return updated_count

# Singleton instance
chroma_manager = ChromaManager()
