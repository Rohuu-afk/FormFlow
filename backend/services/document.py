"""
FormFlow Document Processing Service
=====================================
Handles PDF text extraction and image-based document processing.
Uses pdfplumber for PDF extraction (no Rust/binary dependencies needed).
Returns raw text content that is passed to the AI pipeline.
"""
from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import optional heavy dependencies gracefully
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available. PDF text extraction will be limited.")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not available. Image processing will be limited.")


SUPPORTED_MIME_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "image",
    "image/jpg": "image",
    "image/png": "image",
    "image/webp": "image",
}

MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(20 * 1024 * 1024)))


class DocumentProcessingError(Exception):
    """Raised when document cannot be processed."""
    pass


class ProcessedDocument:
    """Result of document processing."""

    def __init__(
        self,
        raw_text: str,
        page_count: int,
        file_size: int,
        mime_type: str,
        filename: str,
        extraction_method: str,
        page_texts: Optional[list] = None,
    ):
        self.raw_text = raw_text
        self.page_count = page_count
        self.file_size = file_size
        self.mime_type = mime_type
        self.filename = filename
        self.extraction_method = extraction_method
        self.page_texts = page_texts or [raw_text]

    def to_dict(self) -> dict:
        return {
            "raw_text": self.raw_text,
            "page_count": self.page_count,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "filename": self.filename,
            "extraction_method": self.extraction_method,
        }


def validate_upload(filename: str, content: bytes, content_type: str) -> None:
    """
    Validate file before processing.
    Raises DocumentProcessingError with a user-friendly message on failure.
    """
    # Size check
    if len(content) > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE // (1024 * 1024)
        raise DocumentProcessingError(
            f"File size ({len(content) / 1024 / 1024:.1f} MB) exceeds the maximum allowed "
            f"size of {max_mb} MB."
        )

    # Type check (by content-type header)
    if content_type not in SUPPORTED_MIME_TYPES:
        raise DocumentProcessingError(
            f"Unsupported file type: {content_type}. "
            "Accepted types: PDF, JPEG, PNG, WEBP."
        )

    # Extension check
    ext = Path(filename).suffix.lower().lstrip(".")
    allowed_ext = {"pdf", "jpg", "jpeg", "png", "webp"}
    if ext not in allowed_ext:
        raise DocumentProcessingError(
            f"Unsupported file extension: .{ext}. "
            "Accepted extensions: .pdf, .jpg, .jpeg, .png, .webp"
        )

    # Basic magic bytes check for PDF
    if content_type == "application/pdf":
        if not content.startswith(b"%PDF"):
            raise DocumentProcessingError(
                "File does not appear to be a valid PDF (missing PDF header)."
            )

    # Empty file check
    if len(content) < 100:
        raise DocumentProcessingError("File appears to be empty or too small to process.")


def process_document(filename: str, content: bytes, content_type: str) -> ProcessedDocument:
    """
    Main document processing entry point.
    Validates, then extracts text based on file type.
    """
    # Validate first
    validate_upload(filename, content, content_type)

    doc_type = SUPPORTED_MIME_TYPES.get(content_type, "unknown")

    if doc_type == "pdf":
        return _process_pdf(filename, content, content_type)
    elif doc_type == "image":
        return _process_image(filename, content, content_type)
    else:
        raise DocumentProcessingError(f"Cannot process document type: {doc_type}")


def _process_pdf(filename: str, content: bytes, content_type: str) -> ProcessedDocument:
    """Extract text from PDF using pdfplumber."""
    if not PDFPLUMBER_AVAILABLE:
        # Fallback: return placeholder text so AI still gets called
        return ProcessedDocument(
            raw_text="[PDF content — pdfplumber not available, AI will analyze based on filename]",
            page_count=1,
            file_size=len(content),
            mime_type=content_type,
            filename=filename,
            extraction_method="fallback",
        )

    try:
        import io
        page_texts = []
        page_count = 0

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            page_count = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                page_texts.append(f"=== Page {i + 1} ===\n{text}")

        full_text = "\n\n".join(page_texts)

        # If very little text was extracted, the PDF may be scanned
        if len(full_text.strip()) < 50 and page_count > 0:
            logger.info("PDF appears to be image-based or has minimal text. AI will process visually.")
            full_text = f"[Scanned/image-based PDF with {page_count} page(s). Minimal text extracted. AI analysis required.]"
            extraction_method = "pdf_scanned"
        else:
            extraction_method = "pdf_text"

        return ProcessedDocument(
            raw_text=full_text,
            page_count=page_count,
            file_size=len(content),
            mime_type=content_type,
            filename=filename,
            extraction_method=extraction_method,
            page_texts=page_texts,
        )

    except Exception as e:
        logger.error(f"PDF processing error: {e}")
        raise DocumentProcessingError(f"Could not read PDF: {str(e)[:200]}")


def _process_image(filename: str, content: bytes, content_type: str) -> ProcessedDocument:
    """
    Process image documents.
    Images are passed to the AI provider as base64 for visual understanding.
    """
    if not PIL_AVAILABLE:
        return ProcessedDocument(
            raw_text="[Image document — will be processed by AI vision]",
            page_count=1,
            file_size=len(content),
            mime_type=content_type,
            filename=filename,
            extraction_method="image_fallback",
        )

    try:
        import io
        img = Image.open(io.BytesIO(content))
        width, height = img.size
        mode = img.mode

        return ProcessedDocument(
            raw_text=(
                f"[Image document: {width}x{height} {mode}, "
                f"{content_type}, {len(content) // 1024}KB. "
                "Content will be analyzed by AI vision.]"
            ),
            page_count=1,
            file_size=len(content),
            mime_type=content_type,
            filename=filename,
            extraction_method="image",
        )
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        raise DocumentProcessingError(f"Could not read image: {str(e)[:200]}")


def get_document_as_base64(content: bytes, content_type: str) -> str:
    """Return base64-encoded document for AI vision APIs."""
    import base64
    return base64.standard_b64encode(content).decode("utf-8")
