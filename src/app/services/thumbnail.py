import logging
from pathlib import Path
from PIL import Image

from ..config import settings

logger = logging.getLogger(__name__)

class ThumbnailService:
    def __init__(self):
        self.size = settings.THUMBNAIL_SIZE
        self.quality = settings.THUMBNAIL_QUALITY
        self.output_dir = settings.THUMBNAILS_DIR

    def generate(self, image_path: Path, output_name: str = None) -> Path:
        """Generate a thumbnail for an image."""
        try:
            if output_name is None:
                output_name = f"{image_path.stem}_thumb.webp"

            output_path = self.output_dir / output_name

            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for PNG with transparency)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # Create thumbnail maintaining aspect ratio
                img.thumbnail(self.size, Image.Resampling.LANCZOS)

                # Save as WebP for better compression
                img.save(output_path, "WEBP", quality=self.quality)

            logger.debug(f"Generated thumbnail: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {image_path}: {e}")
            raise

    def delete(self, thumbnail_path: Path) -> bool:
        """Delete a thumbnail file."""
        try:
            if thumbnail_path.exists():
                thumbnail_path.unlink()
                logger.debug(f"Deleted thumbnail: {thumbnail_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete thumbnail {thumbnail_path}: {e}")
            return False

thumbnail_service = ThumbnailService()
