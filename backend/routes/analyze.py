"""
FormFlow Upload & Analysis Routes
===================================
POST /api/analyze        — Upload document + analyze → FormDocument schema
POST /api/analyze/demo   — Return demo form without any upload
"""
from __future__ import annotations
import logging
import os
import tempfile
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from models.schema import AnalyzeResponse, DocumentMetadata, FormDocument
from services.document import (
    DocumentProcessingError,
    get_document_as_base64,
    process_document,
)
from services.ai_provider import create_ai_provider

logger = logging.getLogger(__name__)
router = APIRouter()

# Shared AI provider instance (initialized once)
_ai_provider = None
_ai_mode = None


def _get_provider():
    global _ai_provider, _ai_mode
    if _ai_provider is None:
        _ai_provider, _ai_mode = create_ai_provider()
    return _ai_provider, _ai_mode


@router.post("/analyze/demo", response_model=AnalyzeResponse)
async def analyze_demo():
    """
    Return the built-in demo form document without any file upload.
    Always works, no API key required.
    """
    from services.demo_data import get_demo_form_document
    provider, mode = _get_provider()
    doc = get_demo_form_document()
    session_id = str(uuid.uuid4())
    return AnalyzeResponse(
        session_id=session_id,
        form_document=doc,
        mode="demo",
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    file: UploadFile = File(..., description="Form document to analyze (PDF/JPG/PNG/WEBP)"),
):
    """
    Upload and analyze a real document.
    Uses AI if configured; otherwise falls back to demo mode with a notice.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided.",
        )

    provider, mode = _get_provider()

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read the uploaded file.",
        )

    # Validate and process
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "upload"

    try:
        processed = process_document(filename, content, content_type)
    except DocumentProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected document processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the document.",
        )

    # AI analysis
    try:
        schema_dict = await provider.analyze_document(
            raw_text=processed.raw_text,
            filename=filename,
            page_count=processed.page_count,
            file_content=content if content_type.startswith("image/") else None,
            content_type=content_type,
        )
    except RuntimeError as e:
        # AI failed — provide useful error rather than crash
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI analysis failed. Please try again or use Demo Mode.",
        )

    # Update metadata with actual file info
    if "metadata" in schema_dict:
        schema_dict["metadata"]["file_size_bytes"] = processed.file_size
        schema_dict["metadata"]["mime_type"] = content_type
        schema_dict["metadata"]["original_filename"] = filename
        schema_dict["metadata"]["page_count"] = processed.page_count

    # Validate with Pydantic
    try:
        form_doc = FormDocument(**schema_dict)
    except Exception as e:
        logger.error(f"Schema validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI returned data in an unexpected format. Please try again.",
        )

    session_id = str(uuid.uuid4())
    return AnalyzeResponse(
        session_id=session_id,
        form_document=form_doc,
        mode=mode,
    )
