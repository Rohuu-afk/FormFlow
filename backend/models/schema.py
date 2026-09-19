"""
FormFlow Pydantic Schema Models
All models that flow between frontend and backend must match exactly.
"""
from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    FILE = "file"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Field Source
# ---------------------------------------------------------------------------

class FieldSource(BaseModel):
    page: int = 1
    original_label: str = ""
    section: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    excerpt: Optional[str] = None  # raw text from document near this field


# ---------------------------------------------------------------------------
# Validation Rule (stored in schema, evaluated by validation engine)
# ---------------------------------------------------------------------------

class ValidationRule(BaseModel):
    type: str  # required | min_length | max_length | pattern | min_value | max_value | date_range
    value: Optional[Any] = None
    message: str


# ---------------------------------------------------------------------------
# Form Field
# ---------------------------------------------------------------------------

class FormField(BaseModel):
    id: str
    section_id: str
    label: str
    type: FieldType
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None          # for select/radio
    validation: Optional[List[ValidationRule]] = None
    source: Optional[FieldSource] = None
    default_value: Optional[Any] = None
    help_text: Optional[str] = None


# ---------------------------------------------------------------------------
# Form Section
# ---------------------------------------------------------------------------

class FormSection(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    fields: List[FormField]
    order: int = 0
    icon: Optional[str] = None  # emoji or icon name


# ---------------------------------------------------------------------------
# Required Document
# ---------------------------------------------------------------------------

class RequiredDocument(BaseModel):
    id: str
    name: str
    description: str
    required: bool = True
    accepted_formats: List[str] = ["pdf", "jpg", "jpeg", "png", "webp"]
    max_size_mb: int = 20
    extractable_fields: Optional[List[str]] = None  # field ids to cross-check


# ---------------------------------------------------------------------------
# Document Metadata
# ---------------------------------------------------------------------------

class DocumentMetadata(BaseModel):
    source_type: str = "upload"       # upload | demo
    original_filename: Optional[str] = None
    page_count: int = 0
    file_size_bytes: int = 0
    mime_type: Optional[str] = None
    extraction_method: str = "ai"     # ai | demo | ocr | text
    is_demo: bool = False


# ---------------------------------------------------------------------------
# Form Document (root schema)
# ---------------------------------------------------------------------------

class FormDocument(BaseModel):
    id: str
    title: str
    description: str
    sections: List[FormSection]
    required_documents: List[RequiredDocument] = Field(default_factory=list)
    metadata: DocumentMetadata


# ---------------------------------------------------------------------------
# Validation Issue
# ---------------------------------------------------------------------------

class ValidationIssue(BaseModel):
    id: str
    severity: IssueSeverity
    title: str
    description: str
    field_id: Optional[str] = None
    document_ref: Optional[str] = None
    suggested_action: Optional[str] = None
    source: Optional[str] = None


# ---------------------------------------------------------------------------
# Application Check Result
# ---------------------------------------------------------------------------

class CheckCategory(BaseModel):
    name: str
    status: str  # passed | warning | failed
    detail: str


class ApplicationCheckResult(BaseModel):
    overall_status: str  # clean | warning | error
    categories: List[CheckCategory]
    issues: List[ValidationIssue]
    completion_percentage: float
    required_fields_complete: int
    required_fields_total: int
    documents_uploaded: int
    documents_required: int


# ---------------------------------------------------------------------------
# API Request / Response Models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    demo: bool = False


class AnalyzeResponse(BaseModel):
    session_id: str
    form_document: FormDocument
    mode: str  # "demo" | "real"


class ValidateRequest(BaseModel):
    session_id: str
    values: Dict[str, Any]
    uploaded_document_ids: List[str] = Field(default_factory=list)


class ValidateResponse(BaseModel):
    issues: List[ValidationIssue]


class ExportRequest(BaseModel):
    session_id: str
    form_document: FormDocument
    values: Dict[str, Any]
    issues: List[ValidationIssue]
    uploaded_documents: List[str] = Field(default_factory=list)


class ExportResponse(BaseModel):
    filename: str
    download_url: str


class HealthResponse(BaseModel):
    status: str
    ai_configured: bool
    ai_provider: str
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
