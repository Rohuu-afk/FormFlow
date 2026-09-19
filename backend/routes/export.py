"""
FormFlow Export Routes
========================
POST /api/export         — Generate application summary PDF
POST /api/export/demo    — Demo export (no session required)
"""
from __future__ import annotations
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from models.schema import FormDocument, ValidationIssue
from services.pdf_export import generate_export_pdf
from services.demo_data import get_demo_form_document, DEMO_PREFILLED_VALUES

logger = logging.getLogger(__name__)
router = APIRouter()


class ExportRequest(BaseModel):
    form_document: FormDocument
    values: Dict[str, Any] = Field(default_factory=dict)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    uploaded_documents: List[str] = Field(default_factory=list)


class DemoExportRequest(BaseModel):
    values: Optional[Dict[str, Any]] = None
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    uploaded_documents: List[str] = Field(default_factory=list)


@router.post("/export")
async def export_pdf(request: ExportRequest):
    """
    Generate and return the Application Summary PDF.
    Returns the PDF as a binary response with content-disposition header.
    """
    try:
        pdf_bytes = generate_export_pdf(
            form_document=request.form_document.model_dump(),
            values=request.values,
            issues=request.issues,
            uploaded_documents=request.uploaded_documents,
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(e)[:200]}",
        )

    safe_title = "formflow_application_summary"
    filename = f"{safe_title}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.post("/export/demo")
async def export_demo_pdf(request: DemoExportRequest):
    """
    Generate demo application summary PDF.
    Uses demo form data and pre-filled values.
    """
    try:
        doc = get_demo_form_document()
        values = request.values or DEMO_PREFILLED_VALUES

        pdf_bytes = generate_export_pdf(
            form_document=doc.model_dump(),
            values=values,
            issues=request.issues,
            uploaded_documents=request.uploaded_documents,
        )
    except Exception as e:
        logger.error(f"Demo PDF generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo PDF generation failed: {str(e)[:200]}",
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="formflow_demo_summary.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
