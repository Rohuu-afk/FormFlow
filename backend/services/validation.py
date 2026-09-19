"""
FormFlow Validation Engine
===========================
Centralized validation service. Validation logic lives HERE, not in components.

Validates:
- Required fields
- Format checks (email, phone, IFSC, Aadhaar, PIN)
- Numeric range checks
- Date checks
- Cross-field checks
- Cross-document checks (detects mismatches between form values and supporting docs)
- Document requirement checks

Each issue has: id, severity, title, description, field_id?, document_ref?, suggested_action?
"""
from __future__ import annotations
import re
import logging
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from models.schema import (
    FormDocument, FormField, FormSection, FieldType,
    ValidationIssue, IssueSeverity, ValidationRule
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: currency normalization
# ---------------------------------------------------------------------------

def _to_float(value: Any) -> Optional[float]:
    """Convert a value to float, stripping currency symbols and commas."""
    if value is None:
        return None
    try:
        s = str(value).strip().replace(",", "").replace("₹", "").replace("$", "").strip()
        return float(s) if s else None
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Individual field validation
# ---------------------------------------------------------------------------

def _validate_field(
    field: FormField,
    value: Any,
    all_values: Dict[str, Any],
) -> List[ValidationIssue]:
    """Run all validation rules for a single field."""
    issues: List[ValidationIssue] = []

    is_empty = (
        value is None
        or (isinstance(value, str) and value.strip() == "")
        or (isinstance(value, bool) and field.type == FieldType.CHECKBOX and not value)
    )

    # Required check
    if field.required and is_empty:
        issues.append(ValidationIssue(
            id=str(uuid.uuid4()),
            severity=IssueSeverity.ERROR,
            title=f"Required field missing: {field.label}",
            description=f"\"{field.label}\" is required but has not been filled in.",
            field_id=field.id,
            suggested_action="Please fill in this field.",
            source=field.source.section if field.source else None,
        ))
        return issues  # No point checking further if empty

    if is_empty:
        return issues  # Optional and empty — fine

    # Type-specific validation
    str_value = str(value).strip()

    if field.type == FieldType.EMAIL:
        pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, str_value):
            issues.append(ValidationIssue(
                id=str(uuid.uuid4()),
                severity=IssueSeverity.ERROR,
                title=f"Invalid email: {field.label}",
                description=f"'{str_value}' does not appear to be a valid email address.",
                field_id=field.id,
                suggested_action="Enter a valid email address (e.g., name@example.com).",
            ))

    elif field.type == FieldType.PHONE:
        digits = re.sub(r"\D", "", str_value)
        if not re.match(r"^[6-9]\d{9}$", digits):
            issues.append(ValidationIssue(
                id=str(uuid.uuid4()),
                severity=IssueSeverity.ERROR,
                title=f"Invalid phone number: {field.label}",
                description=f"'{str_value}' is not a valid 10-digit Indian mobile number.",
                field_id=field.id,
                suggested_action="Enter a 10-digit mobile number starting with 6, 7, 8, or 9.",
            ))

    elif field.type == FieldType.DATE:
        parsed = _parse_date(str_value)
        if parsed is None:
            issues.append(ValidationIssue(
                id=str(uuid.uuid4()),
                severity=IssueSeverity.ERROR,
                title=f"Invalid date: {field.label}",
                description=f"'{str_value}' is not a recognized date format.",
                field_id=field.id,
                suggested_action="Enter date in YYYY-MM-DD format.",
            ))
        elif parsed > date.today():
            issues.append(ValidationIssue(
                id=str(uuid.uuid4()),
                severity=IssueSeverity.WARNING,
                title=f"Future date: {field.label}",
                description=f"The date '{str_value}' is in the future.",
                field_id=field.id,
                suggested_action="Verify this date is correct.",
            ))

    elif field.type in (FieldType.NUMBER, FieldType.CURRENCY):
        num = _to_float(str_value)
        if num is None:
            issues.append(ValidationIssue(
                id=str(uuid.uuid4()),
                severity=IssueSeverity.ERROR,
                title=f"Invalid number: {field.label}",
                description=f"'{str_value}' is not a valid number.",
                field_id=field.id,
                suggested_action="Enter a numeric value.",
            ))

    # Schema-level validation rules
    if field.validation:
        for rule in field.validation:
            rule_issues = _apply_rule(field, rule, str_value, value)
            issues.extend(rule_issues)

    return issues


def _apply_rule(
    field: FormField,
    rule: ValidationRule,
    str_value: str,
    raw_value: Any,
) -> List[ValidationIssue]:
    """Apply a single validation rule and return any issues."""
    issues: List[ValidationIssue] = []

    def make_issue(severity: IssueSeverity = IssueSeverity.ERROR) -> ValidationIssue:
        return ValidationIssue(
            id=str(uuid.uuid4()),
            severity=severity,
            title=f"{field.label}: {rule.message}",
            description=rule.message,
            field_id=field.id,
            suggested_action=f"Please correct the value for '{field.label}'.",
        )

    if rule.type == "required":
        pass  # Already handled above

    elif rule.type == "min_length":
        if rule.value is not None and len(str_value) < int(rule.value):
            issues.append(make_issue())

    elif rule.type == "max_length":
        if rule.value is not None and len(str_value) > int(rule.value):
            issues.append(make_issue())

    elif rule.type == "pattern":
        if rule.value and not re.match(str(rule.value), str_value):
            issues.append(make_issue())

    elif rule.type == "min_value":
        num = _to_float(str_value)
        if num is not None and rule.value is not None and num < float(rule.value):
            issues.append(make_issue())

    elif rule.type == "max_value":
        num = _to_float(str_value)
        if num is not None and rule.value is not None and num > float(rule.value):
            issues.append(make_issue(IssueSeverity.WARNING))

    return issues


def _parse_date(value: str) -> Optional[date]:
    """Try parsing a date from common formats."""
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d %b %Y", "%d %B %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Cross-document validation
# ---------------------------------------------------------------------------

def _validate_cross_document(
    form_document: FormDocument,
    values: Dict[str, Any],
    extracted_doc_data: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[ValidationIssue]:
    """
    Compare values entered by user against values extracted from supporting documents.
    Returns mismatch warnings.
    """
    issues: List[ValidationIssue] = []
    if not extracted_doc_data:
        return issues

    for doc_id, extracted_fields in extracted_doc_data.items():
        for field_id, extracted_value in extracted_fields.items():
            if field_id not in values:
                continue

            user_value = values[field_id]

            # Normalize for comparison
            user_str = _normalize_value(user_value)
            extracted_str = _normalize_value(extracted_value)

            # Numeric comparison for currency/number fields
            user_num = _to_float(user_str)
            ext_num = _to_float(extracted_str)

            if user_num is not None and ext_num is not None:
                # Allow 1% tolerance for rounding differences
                if abs(user_num - ext_num) > max(1.0, abs(user_num) * 0.01):
                    # Find field label
                    label = _get_field_label(form_document, field_id)
                    issues.append(ValidationIssue(
                        id=str(uuid.uuid4()),
                        severity=IssueSeverity.WARNING,
                        title=f"Potential mismatch: {label}",
                        description=(
                            f"The value you entered ({_format_value(user_num, field_id)}) "
                            f"differs from what was found in the supporting document "
                            f"({_format_value(ext_num, field_id)}). "
                            f"Please verify this is correct."
                        ),
                        field_id=field_id,
                        document_ref=doc_id,
                        suggested_action=(
                            f"Check the {_doc_name(doc_id)} and verify the correct value. "
                            "The supporting document value takes precedence for official records."
                        ),
                        source=f"Cross-check: Application vs {_doc_name(doc_id)}",
                    ))
            elif user_str and extracted_str and user_str.lower() != extracted_str.lower():
                # String comparison (names, etc.)
                label = _get_field_label(form_document, field_id)
                # Only flag significant differences (not just whitespace/case)
                if _significant_string_difference(user_str, extracted_str):
                    issues.append(ValidationIssue(
                        id=str(uuid.uuid4()),
                        severity=IssueSeverity.WARNING,
                        title=f"Potential mismatch: {label}",
                        description=(
                            f"The value you entered ('{user_str}') "
                            f"may differ from the supporting document ('{extracted_str}'). "
                            "Please verify."
                        ),
                        field_id=field_id,
                        document_ref=doc_id,
                        suggested_action=f"Compare your entry against the {_doc_name(doc_id)}.",
                        source=f"Cross-check: Application vs {_doc_name(doc_id)}",
                    ))

    return issues


def _normalize_value(value: Any) -> str:
    """Normalize a value for comparison."""
    if value is None:
        return ""
    return str(value).strip().replace(",", "").replace("₹", "").replace("  ", " ")


def _format_value(num: float, field_id: str) -> str:
    """Format a numeric value for display."""
    if "income" in field_id or "amount" in field_id or "fee" in field_id or "salary" in field_id:
        return f"₹{num:,.0f}"
    return str(num)


def _doc_name(doc_id: str) -> str:
    """Human-readable document name from ID."""
    names = {
        "income_certificate": "Income Certificate",
        "aadhaar_card": "Aadhaar Card",
        "marksheet": "Mark Sheet",
        "bank_passbook": "Bank Passbook",
        "photograph": "Photograph",
    }
    return names.get(doc_id, doc_id.replace("_", " ").title())


def _get_field_label(form_document: FormDocument, field_id: str) -> str:
    """Find a field's label by ID."""
    for section in form_document.sections:
        for field in section.fields:
            if field.id == field_id:
                return field.label
    return field_id


def _significant_string_difference(a: str, b: str) -> bool:
    """Return True if two strings are meaningfully different."""
    a_clean = re.sub(r"\s+", " ", a.lower().strip())
    b_clean = re.sub(r"\s+", " ", b.lower().strip())
    if a_clean == b_clean:
        return False
    # If one is a substring of the other (common for partial name matches), be lenient
    if a_clean in b_clean or b_clean in a_clean:
        return False
    return True


# ---------------------------------------------------------------------------
# Document completeness check
# ---------------------------------------------------------------------------

def _validate_documents(
    form_document: FormDocument,
    uploaded_document_ids: List[str],
) -> List[ValidationIssue]:
    """Check whether required supporting documents have been uploaded."""
    issues: List[ValidationIssue] = []
    for req_doc in form_document.required_documents:
        if req_doc.required and req_doc.id not in uploaded_document_ids:
            issues.append(ValidationIssue(
                id=str(uuid.uuid4()),
                severity=IssueSeverity.WARNING,
                title=f"Missing document: {req_doc.name}",
                description=f"'{req_doc.name}' is required but has not been uploaded.",
                document_ref=req_doc.id,
                suggested_action=f"Upload a clear copy of your {req_doc.name}.",
                source="Document Requirements",
            ))
    return issues


# ---------------------------------------------------------------------------
# Main validation entry point
# ---------------------------------------------------------------------------

def validate_application(
    form_document: FormDocument,
    values: Dict[str, Any],
    uploaded_document_ids: Optional[List[str]] = None,
    extracted_doc_data: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[ValidationIssue]:
    """
    Run full application validation.
    Returns all issues found, sorted by severity (errors first).
    """
    issues: List[ValidationIssue] = []

    # 1. Field-level validation
    for section in form_document.sections:
        for field in section.fields:
            value = values.get(field.id)
            field_issues = _validate_field(field, value, values)
            issues.extend(field_issues)

    # 2. Document completeness
    if uploaded_document_ids is not None:
        doc_issues = _validate_documents(form_document, uploaded_document_ids)
        issues.extend(doc_issues)

    # 3. Cross-document validation
    if extracted_doc_data:
        cross_issues = _validate_cross_document(form_document, values, extracted_doc_data)
        issues.extend(cross_issues)

    # Sort: errors first, then warnings, then info
    severity_order = {IssueSeverity.ERROR: 0, IssueSeverity.WARNING: 1, IssueSeverity.INFO: 2}
    issues.sort(key=lambda i: severity_order.get(i.severity, 99))

    return issues


# ---------------------------------------------------------------------------
# Application check (higher-level summary)
# ---------------------------------------------------------------------------

def perform_application_check(
    form_document: FormDocument,
    values: Dict[str, Any],
    uploaded_document_ids: Optional[List[str]] = None,
    extracted_doc_data: Optional[Dict[str, Dict[str, Any]]] = None,
) -> dict:
    """
    Perform a comprehensive application check.
    Returns structured result for the frontend check panel.
    """
    from models.schema import ApplicationCheckResult, CheckCategory

    issues = validate_application(
        form_document, values, uploaded_document_ids, extracted_doc_data
    )

    # Count required fields
    required_fields = [
        f for s in form_document.sections for f in s.fields if f.required
    ]
    completed_required = sum(
        1 for f in required_fields
        if values.get(f.id) not in (None, "", False)
    )
    total_required = len(required_fields)

    # Count all filled fields
    all_fields = [f for s in form_document.sections for f in s.fields]
    filled_fields = sum(
        1 for f in all_fields
        if values.get(f.id) not in (None, "", False)
    )
    total_fields = len(all_fields)

    completion_pct = (filled_fields / total_fields * 100) if total_fields else 0

    # Documents
    required_docs = [d for d in form_document.required_documents if d.required]
    docs_uploaded = len(uploaded_document_ids or [])
    docs_required = len(required_docs)

    # Count issues by type
    errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
    warnings = [i for i in issues if i.severity == IssueSeverity.WARNING]

    # Category statuses
    categories = []

    # Completeness
    if completed_required == total_required:
        categories.append(CheckCategory(
            name="Required Fields",
            status="passed",
            detail=f"All {total_required} required fields completed.",
        ))
    else:
        missing = total_required - completed_required
        categories.append(CheckCategory(
            name="Required Fields",
            status="failed" if missing > 0 else "passed",
            detail=f"{completed_required} of {total_required} required fields completed. {missing} missing.",
        ))

    # Documents
    if docs_uploaded >= docs_required:
        categories.append(CheckCategory(
            name="Supporting Documents",
            status="passed",
            detail=f"All {docs_required} required documents uploaded.",
        ))
    else:
        missing_docs = docs_required - docs_uploaded
        categories.append(CheckCategory(
            name="Supporting Documents",
            status="warning",
            detail=f"{docs_uploaded} of {docs_required} required documents uploaded. {missing_docs} missing.",
        ))

    # Data validity
    field_errors = [i for i in errors if i.field_id]
    if not field_errors:
        categories.append(CheckCategory(
            name="Data Validity",
            status="passed",
            detail="All entered values pass format and range checks.",
        ))
    else:
        categories.append(CheckCategory(
            name="Data Validity",
            status="failed",
            detail=f"{len(field_errors)} field error(s) found. Please correct before submitting.",
        ))

    # Cross-document consistency
    cross_issues = [i for i in warnings if i.document_ref]
    if not cross_issues:
        categories.append(CheckCategory(
            name="Document Consistency",
            status="passed",
            detail="No mismatches detected between application and supporting documents.",
        ))
    else:
        categories.append(CheckCategory(
            name="Document Consistency",
            status="warning",
            detail=f"{len(cross_issues)} potential mismatch(es) found. Review before submitting.",
        ))

    # Overall status
    if errors:
        overall = "error"
    elif warnings:
        overall = "warning"
    else:
        overall = "clean"

    return ApplicationCheckResult(
        overall_status=overall,
        categories=categories,
        issues=issues,
        completion_percentage=round(completion_pct, 1),
        required_fields_complete=completed_required,
        required_fields_total=total_required,
        documents_uploaded=docs_uploaded,
        documents_required=docs_required,
    ).model_dump()

