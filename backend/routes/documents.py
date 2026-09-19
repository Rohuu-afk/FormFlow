"""
FormFlow Supporting Document Upload Routes
============================================
POST /api/documents/upload  — Upload a supporting document and extract data
GET  /api/documents/{doc_id} — Get metadata about an uploaded document
"""
from __future__ import annotations
import base64
import logging
import os
import tempfile
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from services.document import DocumentProcessingError, process_document
from services.demo_data import DEMO_SUPPORTING_DOCS_EXTRACTED

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session document store (demo/development)
# In production this would be a proper session store or DB
_document_store: Dict[str, Dict[str, Any]] = {}


class UploadedDocumentInfo(BaseModel):
    doc_id: str
    upload_id: str
    filename: str
    file_size: int
    page_count: int
    extraction_method: str
    extracted_fields: Dict[str, Any]
    is_demo: bool = False


@router.post("/documents/upload")
async def upload_supporting_document(
    file: UploadFile = File(...),
    doc_id: str = Form(..., description="ID of the required document slot this fills"),
    is_demo: bool = Form(False, description="Whether to use demo extraction data"),
):
    """
    Upload a supporting document.
    Processes the file and extracts available field data.
    Returns extracted fields for cross-validation.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided.",
        )

    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read the uploaded file.",
        )

    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "document"

    # Validate the file
    try:
        processed = process_document(filename, content, content_type)
    except DocumentProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Document processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the document.",
        )

    # Get extracted fields
    # In demo mode or if AI is not extracting from supporting docs,
    # we use demo data to simulate cross-document validation
    extracted_fields: Dict[str, Any] = {}

    if is_demo and doc_id in DEMO_SUPPORTING_DOCS_EXTRACTED:
        extracted_fields = DEMO_SUPPORTING_DOCS_EXTRACTED[doc_id]
    else:
        # For real mode, attempt text extraction and simple pattern matching
        extracted_fields = _extract_fields_from_text(processed.raw_text, doc_id)

    upload_id = str(uuid.uuid4())
    doc_info = {
        "doc_id": doc_id,
        "upload_id": upload_id,
        "filename": filename,
        "file_size": processed.file_size,
        "page_count": processed.page_count,
        "extraction_method": processed.extraction_method,
        "extracted_fields": extracted_fields,
        "is_demo": is_demo,
    }
    _document_store[upload_id] = doc_info

    return doc_info


def _extract_fields_from_text(raw_text: str, doc_id: str) -> Dict[str, Any]:
    """
    Basic pattern-based field extraction from document text.
    This is a heuristic approach — real extraction is done by AI in full mode.
    """
    import re
    extracted: Dict[str, Any] = {}

    if not raw_text or "[" in raw_text[:50]:
        # Scanned/image doc or placeholder text — can't extract
        return extracted

    text = raw_text.lower()

    # Income certificate patterns
    if doc_id == "income_certificate":
        patterns = [
            r"(?:annual|yearly|total)?\s*(?:family|gross)?\s*income[:\s]+(?:rs\.?|inr|₹)?\s*([\d,]+)",
            r"(?:rs\.?|inr|₹)\s*([\d,]+)\s*(?:per annum|pa|p\.a\.|annually)",
            r"income\s+of\s+(?:rs\.?|inr|₹)?\s*([\d,]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    val = int(match.group(1).replace(",", ""))
                    extracted["annual_family_income"] = str(val)
                    break
                except ValueError:
                    pass

    # Aadhaar card patterns
    elif doc_id == "aadhaar_card":
        aadhaar_match = re.search(r"\b(\d{4}\s\d{4}\s\d{4})\b", raw_text)
        if aadhaar_match:
            extracted["aadhaar_number"] = aadhaar_match.group(1)

    # Mark sheet patterns
    elif doc_id == "marksheet":
        percentage_match = re.search(r"(\d{2,3}\.?\d*)\s*(?:%|percent|percentage)", text)
        if percentage_match:
            extracted["percentage_marks"] = percentage_match.group(1)

    return extracted


@router.get("/documents/{upload_id}")
async def get_document_info(upload_id: str):
    """Get metadata for an uploaded supporting document."""
    if upload_id not in _document_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return _document_store[upload_id]
