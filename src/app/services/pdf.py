import logging
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple
from PIL import Image
import io

logger = logging.getLogger(__name__)


class PDFService:
    def __init__(self, dpi: int = 150):
        self.dpi = dpi
        self.zoom = dpi / 72  # PDF default is 72 DPI

    def extract_pages_as_images(
        self,
        pdf_path: Path,
        output_dir: Path,
        base_name: str
    ) -> List[Tuple[Path, int]]:
        """
        Extract each page from PDF as PNG image.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images
            base_name: Base name for output files (without extension)

        Returns:
            List of tuples: (image_path, page_number)
        """
        results = []
        output_dir.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Render page to pixmap
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert to PNG using PIL for better compression
            output_name = f"{base_name}_page{page_num + 1}.png"
            output_path = output_dir / output_name

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(output_path, "PNG", optimize=True)

            results.append((output_path, page_num + 1))
            logger.debug(f"Extracted page {page_num + 1} to {output_path}")

        doc.close()
        logger.info(f"Extracted {len(results)} pages from {pdf_path.name}")
        return results

    def get_page_count(self, pdf_path: Path) -> int:
        """Get total number of pages in PDF."""
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count


pdf_service = PDFService()
