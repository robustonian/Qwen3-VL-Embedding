import logging
import aiosqlite
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..config import settings

logger = logging.getLogger(__name__)

SCHEMA = """
-- Files table
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    mime_type TEXT,
    file_size INTEGER,
    content_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    thumbnail_path TEXT,
    collection_id TEXT,
    parent_document_id TEXT,
    page_number INTEGER,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_document_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Collections table
CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search history table
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_type TEXT NOT NULL,
    query_text TEXT,
    query_image_path TEXT,
    result_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_files_file_type ON files(file_type);
CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at);
CREATE INDEX IF NOT EXISTS idx_files_collection_id ON files(collection_id);
CREATE INDEX IF NOT EXISTS idx_files_content_hash ON files(content_hash);
CREATE INDEX IF NOT EXISTS idx_files_parent_document_id ON files(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(name);
"""

class SQLiteManager:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or settings.SQLITE_PATH

    async def initialize(self):
        """Initialize database with schema."""
        # Run migrations first for existing databases
        await self._migrate()
        # Then execute full schema (creates tables/indexes if not exist)
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA)
            await db.commit()
        logger.info(f"SQLite database initialized at {self.db_path}")

    async def _migrate(self):
        """Run database migrations for existing databases."""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if files table exists
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='files'"
            )
            if not await cursor.fetchone():
                # Table doesn't exist yet, skip migration
                return

            # Check existing columns
            cursor = await db.execute("PRAGMA table_info(files)")
            columns = [row[1] for row in await cursor.fetchall()]

            # Add parent_document_id if not exists
            if "parent_document_id" not in columns:
                await db.execute("ALTER TABLE files ADD COLUMN parent_document_id TEXT")
                logger.info("Added parent_document_id column to files table")

            # Add page_number if not exists
            if "page_number" not in columns:
                await db.execute("ALTER TABLE files ADD COLUMN page_number INTEGER")
                logger.info("Added page_number column to files table")

            await db.commit()

    async def _execute(self, query: str, params: tuple = ()) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, params)
            await db.commit()

    async def _fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def _fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # ========== File Operations ==========

    async def create_file(
        self,
        file_id: str,
        file_name: str,
        file_path: str,
        file_type: str,
        mime_type: str = None,
        file_size: int = None,
        content_hash: str = None,
        thumbnail_path: str = None,
        collection_id: str = None,
        parent_document_id: str = None,
        page_number: int = None
    ) -> Dict:
        query = """
        INSERT INTO files (id, file_name, file_path, file_type, mime_type, file_size, content_hash, thumbnail_path, collection_id, parent_document_id, page_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self._execute(query, (
            file_id, file_name, file_path, file_type, mime_type,
            file_size, content_hash, thumbnail_path, collection_id,
            parent_document_id, page_number
        ))
        return await self.get_file(file_id)

    async def get_file(self, file_id: str) -> Optional[Dict]:
        query = "SELECT * FROM files WHERE id = ?"
        return await self._fetch_one(query, (file_id,))

    async def get_file_by_hash(self, content_hash: str) -> Optional[Dict]:
        """Get a file by its content hash (for duplicate detection)."""
        query = "SELECT * FROM files WHERE content_hash = ?"
        return await self._fetch_one(query, (content_hash,))

    async def get_files(
        self,
        limit: int = 50,
        offset: int = 0,
        file_types: List[str] = None,
        collection_id: str = None,
        order_by: str = "created_at",
        order_dir: str = "DESC"
    ) -> List[Dict]:
        conditions = []
        params = []

        if file_types:
            placeholders = ",".join("?" * len(file_types))
            conditions.append(f"file_type IN ({placeholders})")
            params.extend(file_types)
        if collection_id:
            conditions.append("collection_id = ?")
            params.append(collection_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
        SELECT * FROM files
        {where_clause}
        ORDER BY {order_by} {order_dir}
        LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        return await self._fetch_all(query, tuple(params))

    async def count_files(self, file_types: List[str] = None, collection_id: str = None) -> int:
        conditions = []
        params = []

        if file_types:
            placeholders = ",".join("?" * len(file_types))
            conditions.append(f"file_type IN ({placeholders})")
            params.extend(file_types)
        if collection_id:
            conditions.append("collection_id = ?")
            params.append(collection_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT COUNT(*) as count FROM files {where_clause}"

        result = await self._fetch_one(query, tuple(params))
        return result["count"] if result else 0

    async def update_file(self, file_id: str, **kwargs) -> Optional[Dict]:
        if not kwargs:
            return await self.get_file(file_id)

        kwargs["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        query = f"UPDATE files SET {set_clause} WHERE id = ?"
        params = list(kwargs.values()) + [file_id]
        await self._execute(query, tuple(params))
        return await self.get_file(file_id)

    async def delete_file(self, file_id: str) -> bool:
        query = "DELETE FROM files WHERE id = ?"
        await self._execute(query, (file_id,))
        return True

    async def delete_files(self, file_ids: List[str]) -> int:
        placeholders = ",".join("?" * len(file_ids))
        query = f"DELETE FROM files WHERE id IN ({placeholders})"
        await self._execute(query, tuple(file_ids))
        return len(file_ids)

    # ========== Collection Operations ==========

    async def create_collection(self, collection_id: str, name: str, description: str = None) -> Dict:
        query = "INSERT INTO collections (id, name, description) VALUES (?, ?, ?)"
        await self._execute(query, (collection_id, name, description))
        return await self.get_collection(collection_id)

    async def get_collection(self, collection_id: str) -> Optional[Dict]:
        query = "SELECT * FROM collections WHERE id = ?"
        return await self._fetch_one(query, (collection_id,))

    async def get_collection_by_name(self, name: str) -> Optional[Dict]:
        query = "SELECT * FROM collections WHERE name = ?"
        return await self._fetch_one(query, (name,))

    async def get_collections(self) -> List[Dict]:
        query = """
        SELECT c.*, COUNT(f.id) as file_count
        FROM collections c
        LEFT JOIN files f ON f.collection_id = c.id
        GROUP BY c.id
        ORDER BY c.created_at DESC
        """
        return await self._fetch_all(query)

    async def update_collection(self, collection_id: str, **kwargs) -> Optional[Dict]:
        if not kwargs:
            return await self.get_collection(collection_id)

        kwargs["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
        query = f"UPDATE collections SET {set_clause} WHERE id = ?"
        params = list(kwargs.values()) + [collection_id]
        await self._execute(query, tuple(params))
        return await self.get_collection(collection_id)

    async def delete_collection(self, collection_id: str) -> bool:
        query = "DELETE FROM collections WHERE id = ?"
        await self._execute(query, (collection_id,))
        return True

    # ========== Search History Operations ==========

    async def add_search_history(
        self,
        query_type: str,
        query_text: str = None,
        query_image_path: str = None,
        result_count: int = 0
    ) -> None:
        query = """
        INSERT INTO search_history (query_type, query_text, query_image_path, result_count)
        VALUES (?, ?, ?, ?)
        """
        await self._execute(query, (query_type, query_text, query_image_path, result_count))

    async def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        query = """
        SELECT * FROM search_history
        ORDER BY created_at DESC
        LIMIT ?
        """
        return await self._fetch_all(query, (limit,))

    # ========== Stats ==========

    async def get_stats(self) -> Dict:
        files_by_type = await self._fetch_all("""
            SELECT file_type, COUNT(*) as count, SUM(file_size) as total_size
            FROM files GROUP BY file_type
        """)

        total_files = await self.count_files()
        total_collections = await self._fetch_one("SELECT COUNT(*) as count FROM collections")

        return {
            "total_files": total_files,
            "total_collections": total_collections["count"] if total_collections else 0,
            "files_by_type": {row["file_type"]: {"count": row["count"], "size": row["total_size"]} for row in files_by_type}
        }

# Singleton instance
sqlite_manager = SQLiteManager()
