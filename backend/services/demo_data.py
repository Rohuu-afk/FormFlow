"""
FormFlow Demo Data
==================
A complete, realistic scholarship application that demonstrates all
FormFlow features without requiring an external AI API key.

The demo contains a deliberate mismatch:
  - User states annual income: ₹2,40,000
  - Income certificate (supporting doc) shows: ₹1,80,000

This mismatch is intentional and is detected by the validation engine.
"""
from __future__ import annotations
import uuid
from models.schema import (
    FormDocument, FormSection, FormField, RequiredDocument,
    DocumentMetadata, FieldType, FieldSource, ConfidenceLevel,
    ValidationRule
)


def get_demo_form_document() -> FormDocument:
    """Return the complete demo form schema."""
    return FormDocument(
        id="demo-scholarship-2024",
        title="National Merit Scholarship Application Form",
        description=(
            "Application for the National Merit Scholarship Programme — "
            "Academic Year 2024-25. Applicants must fill all sections accurately. "
            "Supporting documents must be uploaded as specified."
        ),
        metadata=DocumentMetadata(
            source_type="demo",
            original_filename="national_merit_scholarship_2024.pdf",
            page_count=6,
            file_size_bytes=1_245_000,
            mime_type="application/pdf",
            extraction_method="demo",
            is_demo=True,
        ),
        sections=[
            # ─────────────────────────────────────────────
            # SECTION 1 — Personal Information
            # ─────────────────────────────────────────────
            FormSection(
                id="personal",
                title="Personal Information",
                description="Basic personal and contact details of the applicant.",
                order=0,
                icon="👤",
                fields=[
                    FormField(
                        id="full_name",
                        section_id="personal",
                        label="Full Name (as per official records)",
                        type=FieldType.TEXT,
                        required=True,
                        placeholder="Enter your full name",
                        help_text="Must match your Aadhaar / government ID exactly.",
                        source=FieldSource(
                            page=1,
                            original_label="Applicant's Full Name",
                            section="PART A – PERSONAL DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="1. Applicant's Full Name (in block letters): ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Full name is required."),
                            ValidationRule(type="min_length", value=3, message="Name must be at least 3 characters."),
                        ],
                    ),
                    FormField(
                        id="date_of_birth",
                        section_id="personal",
                        label="Date of Birth",
                        type=FieldType.DATE,
                        required=True,
                        help_text="Format: DD/MM/YYYY",
                        source=FieldSource(
                            page=1,
                            original_label="Date of Birth",
                            section="PART A – PERSONAL DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="2. Date of Birth (DD/MM/YYYY): ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Date of birth is required."),
                        ],
                    ),
                    FormField(
                        id="gender",
                        section_id="personal",
                        label="Gender",
                        type=FieldType.RADIO,
                        required=True,
                        options=["Male", "Female", "Transgender", "Prefer not to say"],
                        source=FieldSource(
                            page=1,
                            original_label="Gender",
                            section="PART A – PERSONAL DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="3. Gender: ☐ Male ☐ Female ☐ Transgender ☐ Prefer not to say",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Please select a gender."),
                        ],
                    ),
                    FormField(
                        id="category",
                        section_id="personal",
                        label="Category",
                        type=FieldType.SELECT,
                        required=True,
                        options=["General", "OBC", "SC", "ST", "EWS", "PwD"],
                        help_text="As per government classification.",
                        source=FieldSource(
                            page=1,
                            original_label="Category (tick appropriate)",
                            section="PART A – PERSONAL DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="4. Category: ☐ General ☐ OBC ☐ SC ☐ ST ☐ EWS ☐ PwD",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Category is required."),
                        ],
                    ),
                    FormField(
                        id="aadhaar_number",
                        section_id="personal",
                        label="Aadhaar Number",
                        type=FieldType.TEXT,
                        required=True,
                        placeholder="XXXX XXXX XXXX",
                        help_text="12-digit Aadhaar number.",
                        source=FieldSource(
                            page=1,
                            original_label="Aadhaar Card Number",
                            section="PART A – PERSONAL DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="5. Aadhaar Card Number: ___ ___ ___",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Aadhaar number is required."),
                            ValidationRule(type="pattern", value=r"^\d{4}\s?\d{4}\s?\d{4}$", message="Enter a valid 12-digit Aadhaar number."),
                        ],
                    ),
                    FormField(
                        id="email",
                        section_id="personal",
                        label="Email Address",
                        type=FieldType.EMAIL,
                        required=True,
                        placeholder="you@example.com",
                        source=FieldSource(
                            page=1,
                            original_label="Email ID",
                            section="PART A – PERSONAL DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="6. Email ID: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Email is required."),
                        ],
                    ),
                    FormField(
                        id="phone",
                        section_id="personal",
                        label="Mobile Number",
                        type=FieldType.PHONE,
                        required=True,
                        placeholder="10-digit mobile number",
                        source=FieldSource(
                            page=1,
                            original_label="Mobile No.",
                            section="PART A – PERSONAL DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="7. Mobile No.: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Mobile number is required."),
                            ValidationRule(type="pattern", value=r"^[6-9]\d{9}$", message="Enter a valid 10-digit Indian mobile number."),
                        ],
                    ),
                ],
            ),

            # ─────────────────────────────────────────────
            # SECTION 2 — Academic Details
            # ─────────────────────────────────────────────
            FormSection(
                id="academic",
                title="Academic Details",
                description="Details of your most recent qualifying examination.",
                order=1,
                icon="🎓",
                fields=[
                    FormField(
                        id="institution_name",
                        section_id="academic",
                        label="Name of Institution / College",
                        type=FieldType.TEXT,
                        required=True,
                        placeholder="Full official name",
                        source=FieldSource(
                            page=2,
                            original_label="Name of Institution",
                            section="PART B – ACADEMIC DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="8. Name of Institution/College: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Institution name is required."),
                        ],
                    ),
                    FormField(
                        id="course_name",
                        section_id="academic",
                        label="Course / Programme",
                        type=FieldType.TEXT,
                        required=True,
                        placeholder="e.g. B.Tech Computer Science",
                        source=FieldSource(
                            page=2,
                            original_label="Course/Programme Enrolled",
                            section="PART B – ACADEMIC DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="9. Course/Programme Enrolled: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Course name is required."),
                        ],
                    ),
                    FormField(
                        id="year_of_study",
                        section_id="academic",
                        label="Current Year of Study",
                        type=FieldType.SELECT,
                        required=True,
                        options=["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year"],
                        source=FieldSource(
                            page=2,
                            original_label="Year of Study",
                            section="PART B – ACADEMIC DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="10. Year of Study: ☐ 1st ☐ 2nd ☐ 3rd ☐ 4th ☐ 5th",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Year of study is required."),
                        ],
                    ),
                    FormField(
                        id="percentage_marks",
                        section_id="academic",
                        label="Percentage / CGPA in Last Examination",
                        type=FieldType.NUMBER,
                        required=True,
                        placeholder="e.g. 87.5 or 8.9",
                        help_text="Enter percentage (0–100) or CGPA on a 10-point scale.",
                        source=FieldSource(
                            page=2,
                            original_label="Marks/CGPA Obtained in Last Exam",
                            section="PART B – ACADEMIC DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="11. Marks/CGPA Obtained in Last Examination: ___",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Marks/CGPA is required."),
                            ValidationRule(type="min_value", value=0, message="Cannot be negative."),
                            ValidationRule(type="max_value", value=100, message="Cannot exceed 100%."),
                        ],
                    ),
                    FormField(
                        id="board_university",
                        section_id="academic",
                        label="Board / University",
                        type=FieldType.TEXT,
                        required=True,
                        placeholder="Name of the awarding body",
                        source=FieldSource(
                            page=2,
                            original_label="Name of Board/University",
                            section="PART B – ACADEMIC DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="12. Name of Board/University: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Board/University is required."),
                        ],
                    ),
                ],
            ),

            # ─────────────────────────────────────────────
            # SECTION 3 — Financial Information
            # ─────────────────────────────────────────────
            FormSection(
                id="financial",
                title="Financial Information",
                description="Family income details. Must be supported by an income certificate.",
                order=2,
                icon="💰",
                fields=[
                    FormField(
                        id="annual_family_income",
                        section_id="financial",
                        label="Annual Family Income (₹)",
                        type=FieldType.CURRENCY,
                        required=True,
                        placeholder="e.g. 240000",
                        help_text=(
                            "Total gross annual income of all earning members. "
                            "MUST match the income certificate."
                        ),
                        source=FieldSource(
                            page=3,
                            original_label="Annual Family Income (in Rupees)",
                            section="PART C – FINANCIAL DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="13. Annual Family Income (in Rupees): ₹___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Annual family income is required."),
                            ValidationRule(type="min_value", value=0, message="Income cannot be negative."),
                            ValidationRule(type="max_value", value=800000, message="Income exceeds scholarship eligibility limit of ₹8,00,000."),
                        ],
                    ),
                    FormField(
                        id="income_source",
                        section_id="financial",
                        label="Primary Source of Family Income",
                        type=FieldType.SELECT,
                        required=True,
                        options=[
                            "Salaried Employment",
                            "Self-Employed / Business",
                            "Agriculture",
                            "Daily Wages / Labour",
                            "Pension",
                            "Other",
                        ],
                        source=FieldSource(
                            page=3,
                            original_label="Source of Income",
                            section="PART C – FINANCIAL DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="14. Source of Income: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Income source is required."),
                        ],
                    ),
                    FormField(
                        id="bank_account_number",
                        section_id="financial",
                        label="Bank Account Number",
                        type=FieldType.TEXT,
                        required=True,
                        placeholder="Account number for scholarship disbursement",
                        source=FieldSource(
                            page=3,
                            original_label="Bank Account No. (for scholarship disbursement)",
                            section="PART C – FINANCIAL DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="15. Bank Account No.: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Bank account number is required."),
                            ValidationRule(type="min_length", value=9, message="Account number too short."),
                        ],
                    ),
                    FormField(
                        id="ifsc_code",
                        section_id="financial",
                        label="IFSC Code",
                        type=FieldType.TEXT,
                        required=True,
                        placeholder="e.g. SBIN0001234",
                        source=FieldSource(
                            page=3,
                            original_label="Bank IFSC Code",
                            section="PART C – FINANCIAL DETAILS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="16. Bank IFSC Code: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="IFSC code is required."),
                            ValidationRule(type="pattern", value=r"^[A-Z]{4}0[A-Z0-9]{6}$", message="Enter a valid IFSC code (e.g. SBIN0001234)."),
                        ],
                    ),
                ],
            ),

            # ─────────────────────────────────────────────
            # SECTION 4 — Address
            # ─────────────────────────────────────────────
            FormSection(
                id="address",
                title="Address Details",
                description="Permanent residential address.",
                order=3,
                icon="🏠",
                fields=[
                    FormField(
                        id="address_line1",
                        section_id="address",
                        label="Address Line 1",
                        type=FieldType.TEXT,
                        required=True,
                        placeholder="House/Flat No., Building Name, Street",
                        source=FieldSource(
                            page=4,
                            original_label="Permanent Address – Line 1",
                            section="PART D – ADDRESS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="17. Permanent Address: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Address is required."),
                        ],
                    ),
                    FormField(
                        id="city",
                        section_id="address",
                        label="City / Town",
                        type=FieldType.TEXT,
                        required=True,
                        placeholder="City or town name",
                        source=FieldSource(
                            page=4,
                            original_label="City/Town",
                            section="PART D – ADDRESS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="18. City/Town: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="City is required."),
                        ],
                    ),
                    FormField(
                        id="state",
                        section_id="address",
                        label="State",
                        type=FieldType.SELECT,
                        required=True,
                        options=[
                            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
                            "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
                            "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
                            "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                            "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
                            "Uttar Pradesh", "Uttarakhand", "West Bengal",
                            "Delhi", "Jammu & Kashmir", "Ladakh",
                        ],
                        source=FieldSource(
                            page=4,
                            original_label="State",
                            section="PART D – ADDRESS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="19. State: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="State is required."),
                        ],
                    ),
                    FormField(
                        id="pincode",
                        section_id="address",
                        label="PIN Code",
                        type=FieldType.TEXT,
                        required=True,
                        placeholder="6-digit PIN code",
                        source=FieldSource(
                            page=4,
                            original_label="PIN Code",
                            section="PART D – ADDRESS",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="20. PIN Code: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="PIN code is required."),
                            ValidationRule(type="pattern", value=r"^\d{6}$", message="Enter a valid 6-digit PIN code."),
                        ],
                    ),
                ],
            ),

            # ─────────────────────────────────────────────
            # SECTION 5 — Declaration
            # ─────────────────────────────────────────────
            FormSection(
                id="declaration",
                title="Declaration",
                description="Read carefully before submitting.",
                order=4,
                icon="📋",
                fields=[
                    FormField(
                        id="declaration_accept",
                        section_id="declaration",
                        label=(
                            "I hereby declare that all information provided in this application is "
                            "true, complete, and correct to the best of my knowledge. I understand "
                            "that furnishing false information may result in disqualification and "
                            "legal action."
                        ),
                        type=FieldType.CHECKBOX,
                        required=True,
                        source=FieldSource(
                            page=6,
                            original_label="Declaration Checkbox",
                            section="PART F – DECLARATION",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="I hereby declare that... ☐",
                        ),
                        validation=[
                            ValidationRule(type="required", message="You must accept the declaration to submit."),
                        ],
                    ),
                    FormField(
                        id="place_of_signing",
                        section_id="declaration",
                        label="Place",
                        type=FieldType.TEXT,
                        required=True,
                        placeholder="City where you are signing",
                        source=FieldSource(
                            page=6,
                            original_label="Place",
                            section="PART F – DECLARATION",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="Place: ___________ Date: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Place is required."),
                        ],
                    ),
                    FormField(
                        id="date_of_signing",
                        section_id="declaration",
                        label="Date of Signing",
                        type=FieldType.DATE,
                        required=True,
                        source=FieldSource(
                            page=6,
                            original_label="Date",
                            section="PART F – DECLARATION",
                            confidence=ConfidenceLevel.HIGH,
                            excerpt="Date: ___________",
                        ),
                        validation=[
                            ValidationRule(type="required", message="Date of signing is required."),
                        ],
                    ),
                ],
            ),
        ],
        required_documents=[
            RequiredDocument(
                id="aadhaar_card",
                name="Aadhaar Card",
                description="Clear copy of Aadhaar card (front and back). Name and DOB must match application.",
                required=True,
                extractable_fields=["full_name", "date_of_birth", "aadhaar_number"],
            ),
            RequiredDocument(
                id="income_certificate",
                name="Income Certificate",
                description=(
                    "Official income certificate issued by a competent authority "
                    "(Tehsildar / District Magistrate) within the last 6 months."
                ),
                required=True,
                extractable_fields=["annual_family_income"],
            ),
            RequiredDocument(
                id="marksheet",
                name="Last Qualifying Examination Marksheet",
                description="Mark sheet / result card of the most recent examination.",
                required=True,
                extractable_fields=["percentage_marks", "institution_name"],
            ),
            RequiredDocument(
                id="bank_passbook",
                name="Bank Passbook / Cancelled Cheque",
                description="First page of bank passbook or cancelled cheque showing account number and IFSC.",
                required=True,
                extractable_fields=["bank_account_number", "ifsc_code"],
            ),
            RequiredDocument(
                id="photograph",
                name="Passport-size Photograph",
                description="Recent colour photograph with white background (max 100KB).",
                required=True,
                accepted_formats=["jpg", "jpeg", "png"],
                extractable_fields=[],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Demo pre-filled values (simulate user entering data with deliberate mismatch)
# ---------------------------------------------------------------------------

DEMO_PREFILLED_VALUES: dict = {
    "full_name": "Priya Sharma",
    "date_of_birth": "2003-07-15",
    "gender": "Female",
    "category": "General",
    "aadhaar_number": "9876 5432 1012",
    "email": "priya.sharma@example.com",
    "phone": "9876543210",
    "institution_name": "Government Engineering College, Pune",
    "course_name": "B.Tech Computer Science and Engineering",
    "year_of_study": "2nd Year",
    "percentage_marks": "88.5",
    "board_university": "Savitribai Phule Pune University",
    # DELIBERATE MISMATCH: application says 2,40,000 but income certificate shows 1,80,000
    "annual_family_income": "240000",
    "income_source": "Salaried Employment",
    "bank_account_number": "50200012345678",
    "ifsc_code": "HDFC0001234",
    "address_line1": "12, Shivaji Nagar, Near Railway Station",
    "city": "Pune",
    "state": "Maharashtra",
    "pincode": "411005",
    "declaration_accept": True,
    "place_of_signing": "Pune",
    "date_of_signing": "2024-09-19",
}


# ---------------------------------------------------------------------------
# Demo supporting document simulation
# ---------------------------------------------------------------------------

DEMO_SUPPORTING_DOCS_EXTRACTED = {
    "income_certificate": {
        "annual_family_income": "180000",   # ← mismatch vs 240000 in application
        "applicant_name": "Priya Sharma",
    },
    "aadhaar_card": {
        "full_name": "Priya Sharma",        # ← matches
        "date_of_birth": "15/07/2003",      # ← matches (different format)
        "aadhaar_number": "9876 5432 1012", # ← matches
    },
    "marksheet": {
        "percentage_marks": "88.5",         # ← matches
        "institution_name": "Government Engineering College, Pune",
    },
}
