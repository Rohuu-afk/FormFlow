"""
FormFlow Validation Routes
============================
POST /api/validate       — Validate application values + cross-document check
POST /api/check          — Full application check (summary + issues)
POST /api/validate/demo  — Demo validation showing deliberate mismatch
"""
from __future__ import annotations
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from models.schema import (
    FormDocument, ValidationIssue, ApplicationCheckResult
)
from services.validation import validate_application, perform_application_check
from services.demo_data import (
    get_demo_form_document, DEMO_PREFILLED_VALUES, DEMO_SUPPORTING_DOCS_EXTRACTED
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request models (local, for these routes only)
# ---------------------------------------------------------------------------

class ValidateRequest(BaseModel):
    form_document: FormDocument
    values: Dict[str, Any] = Field(default_factory=dict)
    uploaded_document_ids: List[str] = Field(default_factory=list)
    extracted_doc_data: Optional[Dict[str, Dict[str, Any]]] = None


class CheckRequest(BaseModel):
    form_document: FormDocument
    values: Dict[str, Any] = Field(default_factory=dict)
    uploaded_document_ids: List[str] = Field(default_factory=list)
    extracted_doc_data: Optional[Dict[str, Dict[str, Any]]] = None


class DemoValidateRequest(BaseModel):
    uploaded_document_ids: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/validate")
async def validate(request: ValidateRequest):
    """
    Validate an application's values against its schema.
    Optionally performs cross-document validation if extracted_doc_data is provided.
    """
    try:
        issues = validate_application(
            form_document=request.form_document,
            values=request.values,
            uploaded_document_ids=request.uploaded_document_ids,
            extracted_doc_data=request.extracted_doc_data,
        )
        return {"issues": [i.model_dump() for i in issues]}
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation failed due to an unexpected error.",
        )


@router.post("/check")
async def check_application(request: CheckRequest):
    """
    Perform a full application check and return structured summary.
    """
    try:
        result = perform_application_check(
            form_document=request.form_document,
            values=request.values,
            uploaded_document_ids=request.uploaded_document_ids,
            extracted_doc_data=request.extracted_doc_data,
        )
        return result
    except Exception as e:
        logger.error(f"Application check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application check failed due to an unexpected error.",
        )


@router.post("/validate/demo")
async def validate_demo(request: DemoValidateRequest):
    """
    Demo validation — uses pre-filled demo values and simulated extracted docs.
    Always shows the income mismatch warning regardless of uploaded_document_ids.
    """
    try:
        doc = get_demo_form_document()
        # Merge uploaded IDs with demo docs to simulate cross-checking
        uploaded = list(set(request.uploaded_document_ids + ["income_certificate", "aadhaar_card"]))

        issues = validate_application(
            form_document=doc,
            values=DEMO_PREFILLED_VALUES,
            uploaded_document_ids=uploaded,
            extracted_doc_data=DEMO_SUPPORTING_DOCS_EXTRACTED,
        )
        return {"issues": [i.model_dump() for i in issues]}
    except Exception as e:
        logger.error(f"Demo validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo validation failed.",
        )


@router.post("/check/demo")
async def check_demo(request: DemoValidateRequest):
    """Demo application check."""
    try:
        doc = get_demo_form_document()
        uploaded = list(set(request.uploaded_document_ids + ["income_certificate", "aadhaar_card"]))

        result = perform_application_check(
            form_document=doc,
            values=DEMO_PREFILLED_VALUES,
            uploaded_document_ids=uploaded,
            extracted_doc_data=DEMO_SUPPORTING_DOCS_EXTRACTED,
        )
        return result
    except Exception as e:
        logger.error(f"Demo check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo application check failed.",
        )
