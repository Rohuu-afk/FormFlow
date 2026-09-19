"""
FormFlow AI Provider Abstraction
==================================
Provides a unified interface to:
  - Real AI (Google Gemini)
  - Demo provider (deterministic, no API key needed)

The AI provider's job is to take raw document text/images and return
a structured FormDocument schema.
"""
from __future__ import annotations
import json
import logging
import os
import re
import textwrap
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract Base
# ---------------------------------------------------------------------------

class AIProvider(ABC):
    """Abstract AI provider. All providers must implement analyze_document."""

    @abstractmethod
    async def analyze_document(
        self,
        raw_text: str,
        filename: str,
        page_count: int,
        file_content: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> dict:
        """
        Analyze a document and return a dict conforming to FormDocument schema.
        Must always return a valid dict even on partial extraction.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider is properly configured."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...


# ---------------------------------------------------------------------------
# Demo Provider — deterministic, no external calls
# ---------------------------------------------------------------------------

class DemoAIProvider(AIProvider):
    """
    Returns a fixed realistic demo form document.
    Used when no API key is configured or demo mode is requested.
    """

    def is_available(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return "Demo"

    async def analyze_document(
        self,
        raw_text: str,
        filename: str,
        page_count: int,
        file_content: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> dict:
        """Return the demo form schema as a dict."""
        from services.demo_data import get_demo_form_document
        doc = get_demo_form_document()
        return doc.model_dump()


# ---------------------------------------------------------------------------
# Gemini AI Provider
# ---------------------------------------------------------------------------

GEMINI_SYSTEM_PROMPT = textwrap.dedent("""
You are FormFlow's document analysis engine.
Your job is to analyze administrative/government/application forms and extract their structure.

You must return ONLY valid JSON matching the exact schema below. No explanations, no markdown fences.

SCHEMA:
{
  "id": "unique-string",
  "title": "Document title",
  "description": "Brief document description",
  "metadata": {
    "source_type": "upload",
    "original_filename": "filename.pdf",
    "page_count": 3,
    "file_size_bytes": 0,
    "mime_type": "application/pdf",
    "extraction_method": "ai",
    "is_demo": false
  },
  "sections": [
    {
      "id": "section-id",
      "title": "Section Name",
      "description": "Optional section description",
      "order": 0,
      "icon": "📄",
      "fields": [
        {
          "id": "field-id",
          "section_id": "section-id",
          "label": "Field Label",
          "type": "text",
          "required": true,
          "placeholder": "Enter value",
          "options": null,
          "help_text": null,
          "default_value": null,
          "source": {
            "page": 1,
            "original_label": "Original label from document",
            "section": "Section name in original document",
            "confidence": "high",
            "excerpt": "Exact text from document near this field"
          },
          "validation": [
            {"type": "required", "message": "This field is required.", "value": null}
          ]
        }
      ]
    }
  ],
  "required_documents": [
    {
      "id": "doc-id",
      "name": "Document Name",
      "description": "What this document is",
      "required": true,
      "accepted_formats": ["pdf", "jpg", "jpeg", "png", "webp"],
      "max_size_mb": 20,
      "extractable_fields": ["field-id"]
    }
  ]
}

FIELD TYPES (use exactly these strings):
text, textarea, number, currency, date, email, phone, select, radio, checkbox, file

CONFIDENCE LEVELS: high, medium, low

RULES:
1. Identify ALL sections in the document.
2. Extract ALL fields from each section.
3. Preserve original labels in source.original_label.
4. Set appropriate field types (use currency for money fields, date for dates, etc).
5. Mark fields as required if they clearly are in the document.
6. Add options arrays for select/radio fields.
7. Include validation rules for format-sensitive fields.
8. Identify required supporting documents mentioned in the form.
9. Use realistic icon emojis for sections (👤 personal, 🎓 academic, 💰 financial, 🏠 address, 📋 declaration).
10. Return ONLY the JSON object. Nothing else.
""").strip()


class GeminiAIProvider(AIProvider):
    """Google Gemini 1.5 Flash AI provider."""

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = None
        self._model = None
        self._init_client()

    def _init_client(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel(
                model_name="gemini-3.6-flash",
                system_instruction=GEMINI_SYSTEM_PROMPT,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.95,
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json",
                },
            )
            logger.info("Gemini AI provider initialized successfully.")
        except ImportError:
            logger.error("google-generativeai package not installed.")
            self._model = None
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self._model = None

    def is_available(self) -> bool:
        return self._model is not None and bool(self._api_key)

    @property
    def name(self) -> str:
        return "Google Gemini 1.5 Flash"

    async def analyze_document(
        self,
        raw_text: str,
        filename: str,
        page_count: int,
        file_content: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> dict:
        if not self.is_available():
            raise RuntimeError("Gemini AI provider is not available.")

        import asyncio

        # Build prompt
        user_prompt = (
            f"Analyze the following document and extract its form structure.\n"
            f"Filename: {filename}\n"
            f"Pages: {page_count}\n\n"
            f"DOCUMENT CONTENT:\n{raw_text[:12000]}"  # Limit to avoid token overflow
        )

        # For image-based documents, include the image
        parts = [user_prompt]
        is_image = content_type and content_type.startswith("image/")

        if is_image and file_content:
            try:
                import google.generativeai as genai
                image_part = {
                    "mime_type": content_type,
                    "data": file_content,
                }
                parts = [user_prompt, image_part]
            except Exception as e:
                logger.warning(f"Could not attach image to AI request: {e}")

        # Run in executor to avoid blocking (Gemini SDK is sync)
        loop = asyncio.get_event_loop()
        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self._model.generate_content(parts)),
                timeout=60.0,
            )
        except asyncio.TimeoutError:
            raise RuntimeError("AI analysis timed out after 60 seconds. Please try again.")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"AI analysis failed: {str(e)[:300]}")

        # Parse and validate response
        raw_json = response.text if response.text else ""
        return self._parse_and_validate(raw_json, filename, page_count, content_type)

    def _parse_and_validate(
        self,
        raw_json: str,
        filename: str,
        page_count: int,
        content_type: Optional[str],
    ) -> dict:
        """Parse AI JSON response and ensure it conforms to our schema."""
        # Strip markdown fences if present
        cleaned = raw_json.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"AI returned invalid JSON: {e}\nRaw: {raw_json[:500]}")
            raise RuntimeError("AI returned malformed response. Please try again.")

        # Ensure required top-level fields exist
        if "sections" not in data or not data["sections"]:
            raise RuntimeError("AI did not extract any form sections from the document.")

        # Inject/fix metadata
        if "metadata" not in data:
            data["metadata"] = {}
        data["metadata"].update({
            "source_type": "upload",
            "original_filename": filename,
            "page_count": page_count,
            "extraction_method": "ai",
            "is_demo": False,
            "mime_type": content_type or "application/octet-stream",
        })

        # Ensure ID
        if not data.get("id"):
            data["id"] = str(uuid.uuid4())

        # Ensure title
        if not data.get("title"):
            data["title"] = f"Extracted Form — {filename}"

        # Ensure required_documents list
        if "required_documents" not in data:
            data["required_documents"] = []

        # Normalize sections / fields
        for i, section in enumerate(data.get("sections", [])):
            if not section.get("id"):
                section["id"] = f"section-{i}"
            if "order" not in section:
                section["order"] = i
            for j, field in enumerate(section.get("fields", [])):
                if not field.get("id"):
                    field["id"] = f"{section['id']}-field-{j}"
                if not field.get("section_id"):
                    field["section_id"] = section["id"]
                # Ensure source exists
                if "source" not in field or not field["source"]:
                    field["source"] = {
                        "page": 1,
                        "original_label": field.get("label", ""),
                        "section": section.get("title", ""),
                        "confidence": "medium",
                        "excerpt": None,
                    }
                # Validate field type
                valid_types = {
                    "text", "textarea", "number", "currency", "date",
                    "email", "phone", "select", "radio", "checkbox", "file"
                }
                if field.get("type") not in valid_types:
                    field["type"] = "text"
                # Ensure validation is a list
                if "validation" not in field or field["validation"] is None:
                    field["validation"] = []

        return data


# ---------------------------------------------------------------------------
# Provider Factory
# ---------------------------------------------------------------------------

def create_ai_provider() -> tuple[AIProvider, str]:
    """
    Create the appropriate AI provider based on environment configuration.
    Returns (provider, mode) where mode is 'real' or 'demo'.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if api_key and api_key not in ("", "your-api-key-here"):
        try:
            provider = GeminiAIProvider(api_key)
            if provider.is_available():
                logger.info("Using real Gemini AI provider.")
                return provider, "real"
        except Exception as e:
            logger.warning(f"Failed to create Gemini provider: {e}. Falling back to demo.")

    logger.info("Using demo AI provider (no valid API key configured).")
    return DemoAIProvider(), "demo"
