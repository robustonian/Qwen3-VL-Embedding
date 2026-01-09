import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"

    # Upload paths
    UPLOADS_DIR: Path = DATA_DIR / "uploads"
    IMAGES_DIR: Path = UPLOADS_DIR / "images"
    DOCUMENTS_DIR: Path = UPLOADS_DIR / "documents"
    THUMBNAILS_DIR: Path = UPLOADS_DIR / "thumbnails"

    # Database paths
    DB_DIR: Path = DATA_DIR / "db"
    CHROMA_DIR: Path = DB_DIR / "chroma"
    SQLITE_PATH: Path = DB_DIR / "metadata.db"

    # ChromaDB settings
    CHROMA_COLLECTION_NAME: str = "multimodal_embeddings"

    # Thumbnail settings
    THUMBNAIL_SIZE: tuple = (256, 256)
    THUMBNAIL_QUALITY: int = 80

    # API settings
    API_PREFIX: str = "/api"
    EMBEDDING_API_URL: str = "http://localhost:8000/v1/embeddings"

    # File settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_IMAGE_TYPES: set = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    ALLOWED_DOCUMENT_TYPES: set = {"application/pdf", "text/plain"}

    class Config:
        env_prefix = "QWEN_SEARCH_"

    def ensure_directories(self):
        """Create all necessary directories if they don't exist."""
        for dir_path in [
            self.UPLOADS_DIR,
            self.IMAGES_DIR,
            self.DOCUMENTS_DIR,
            self.THUMBNAILS_DIR,
            self.DB_DIR,
            self.CHROMA_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
