"""
Smart Inbox Assistant — Google Gemini AI Service
Uses the new google-genai SDK (google-genai >= 2.0).
"""
from google import genai
import json
import logging
import time
import base64
from typing import Optional, List, Dict, Any
from app.config import settings
from app.utils.prompts import (
    CLASSIFICATION_PROMPT,
    ICSR_EXTRACTION_PROMPT,
    PQC_EXTRACTION_PROMPT,
    MI_EXTRACTION_PROMPT,
    SUMMARY_PROMPT,
    IMAGE_DESCRIPTION_PROMPT,
    LITERATURE_SCREENING_PROMPT,
    TRANSLATION_PROMPT,
    HANDWRITING_OCR_PROMPT,
    PDF_TYPE_DETECTION_PROMPT,
)
from app.utils.helpers import safe_json_parse, truncate_text

logger = logging.getLogger(__name__)


class AIService:
    """Google Gemini AI service using the new google-genai SDK."""

    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        logger.info(f"Gemini AI service initialized with model: {self.model_name}")

    def _generate(self, prompt: str, max_retries: int = 3) -> str:
        """Generate text from a prompt using the Gemini model with retry logic."""
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                last_error = e
                error_str = str(e)
                # Retry on 503 (server overloaded) or 429 (rate limit)
                if "503" in error_str or "429" in error_str or "UNAVAILABLE" in error_str or "overloaded" in error_str.lower():
                    wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
                    logger.warning(f"Gemini API temporarily unavailable (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise  # Non-retryable error, raise immediately
        raise last_error  # All retries exhausted

    def _generate_with_image(self, prompt: str, image_bytes: bytes, mime_type: str, max_retries: int = 3) -> str:
        """Generate text from a prompt + image using Gemini vision with retry logic."""
        from google.genai import types
        last_error = None
        for attempt in range(max_retries):
            try:
                image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[prompt, image_part],
                )
                return response.text
            except Exception as e:
                last_error = e
                error_str = str(e)
                if "503" in error_str or "429" in error_str or "UNAVAILABLE" in error_str or "overloaded" in error_str.lower():
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(f"Gemini Vision API temporarily unavailable (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        raise last_error

    async def classify_message(
        self, subject: str, sender: str, body_text: str, attachment_text: str = ""
    ) -> List[Dict[str, Any]]:
        """Classify a message into one or more of the 4 categories."""
        prompt = CLASSIFICATION_PROMPT.format(
            subject=subject or "No subject",
            sender=sender or "Unknown",
            body_text=truncate_text(body_text, 4000),
            attachment_text=truncate_text(attachment_text, 4000),
        )

        start_time = time.time()
        try:
            raw = self._generate(prompt)
            result = safe_json_parse(raw)
            elapsed = int((time.time() - start_time) * 1000)
            logger.info(f"Classification completed in {elapsed}ms")

            if result and isinstance(result, dict):
                result = {k.strip(): v for k, v in result.items()}
                if "classifications" in result:
                    return result["classifications"]
            if isinstance(result, list):
                return result

            logger.warning(f"Unexpected classification response: {raw[:300]}")
            return [{"category": "NOT_RELEVANT", "confidence_score": 0.5,
                     "ai_reason": "AI response could not be parsed."}]
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return [{"category": "NOT_RELEVANT", "confidence_score": 0.0,
                     "ai_reason": f"Classification error: {str(e)}"}]

    async def extract_icsr(
        self, subject: str, sender: str, body_text: str, attachment_text: str = ""
    ) -> Dict[str, Any]:
        """Extract ICSR (safety report) facts from a document."""
        prompt = ICSR_EXTRACTION_PROMPT.format(
            subject=subject or "No subject",
            sender=sender or "Unknown",
            body_text=truncate_text(body_text, 5000),
            attachment_text=truncate_text(attachment_text, 5000),
        )
        start_time = time.time()
        try:
            raw = self._generate(prompt)
            result = safe_json_parse(raw)
            elapsed = int((time.time() - start_time) * 1000)
            logger.info(f"ICSR extraction completed in {elapsed}ms")
            return result if result else {"error": "Could not parse extraction response"}
        except Exception as e:
            logger.error(f"ICSR extraction failed: {e}")
            return {"error": str(e)}

    async def extract_pqc(
        self, subject: str, sender: str, body_text: str, attachment_text: str = ""
    ) -> Dict[str, Any]:
        """Extract PQC (product quality complaint) facts."""
        prompt = PQC_EXTRACTION_PROMPT.format(
            subject=subject or "No subject",
            sender=sender or "Unknown",
            body_text=truncate_text(body_text, 5000),
            attachment_text=truncate_text(attachment_text, 5000),
        )
        try:
            raw = self._generate(prompt)
            result = safe_json_parse(raw)
            return result if result else {"error": "Could not parse response"}
        except Exception as e:
            logger.error(f"PQC extraction failed: {e}")
            return {"error": str(e)}

    async def extract_mi(
        self, subject: str, sender: str, body_text: str, attachment_text: str = ""
    ) -> Dict[str, Any]:
        """Extract MI (medical information request) facts."""
        prompt = MI_EXTRACTION_PROMPT.format(
            subject=subject or "No subject",
            sender=sender or "Unknown",
            body_text=truncate_text(body_text, 5000),
            attachment_text=truncate_text(attachment_text, 5000),
        )
        try:
            raw = self._generate(prompt)
            result = safe_json_parse(raw)
            return result if result else {"error": "Could not parse response"}
        except Exception as e:
            logger.error(f"MI extraction failed: {e}")
            return {"error": str(e)}

    async def summarize_document(
        self, subject: str, sender: str, body_text: str, attachment_text: str = ""
    ) -> str:
        """Generate a 10-15 sentence summary for human review."""
        prompt = SUMMARY_PROMPT.format(
            subject=subject or "No subject",
            sender=sender or "Unknown",
            body_text=truncate_text(body_text, 5000),
            attachment_text=truncate_text(attachment_text, 5000),
        )
        try:
            return self._generate(prompt).strip()
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return f"Summary generation failed: {str(e)}"

    async def describe_image(self, image_bytes: bytes, mime_type: str = "image/png") -> Dict[str, Any]:
        """Describe an image using Gemini vision capabilities."""
        try:
            raw = self._generate_with_image(IMAGE_DESCRIPTION_PROMPT, image_bytes, mime_type)
            result = safe_json_parse(raw)
            return result if result else {
                "description": raw.strip(),
                "flag_for_review": True,
                "flag_reason": "Could not parse structured response"
            }
        except Exception as e:
            logger.error(f"Image description failed: {e}")
            return {
                "description": f"Image analysis failed: {str(e)}",
                "flag_for_review": True,
                "flag_reason": "Image analysis error"
            }

    async def detect_pdf_type(self, text_sample: str) -> Dict[str, Any]:
        """Detect the type of PDF from extracted text."""
        prompt = PDF_TYPE_DETECTION_PROMPT.format(
            text_sample=truncate_text(text_sample, 2000)
        )
        try:
            raw = self._generate(prompt)
            result = safe_json_parse(raw)
            return result if result else {
                "pdf_type": "DIGITAL",
                "detected_language": "English",
                "confidence": 0.5,
                "reasoning": "Default classification"
            }
        except Exception as e:
            logger.error(f"PDF type detection failed: {e}")
            return {
                "pdf_type": "DIGITAL",
                "detected_language": "Unknown",
                "confidence": 0.0,
                "reasoning": f"Detection error: {str(e)}"
            }

    async def translate_text(self, text: str, source_language: str) -> Dict[str, Any]:
        """Translate non-English text to English."""
        prompt = TRANSLATION_PROMPT.format(
            source_language=source_language,
            text=truncate_text(text, 5000),
        )
        try:
            raw = self._generate(prompt)
            result = safe_json_parse(raw)
            return result if result else {
                "translated_text": raw.strip(),
                "source_language": source_language,
                "translation_confidence": 0.5,
            }
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {"translated_text": "", "error": str(e)}

    async def ocr_handwritten(self, image_bytes: bytes, mime_type: str = "image/png") -> Dict[str, Any]:
        """Use Gemini vision to OCR handwritten/scanned documents."""
        try:
            raw = self._generate_with_image(HANDWRITING_OCR_PROMPT, image_bytes, mime_type)
            result = safe_json_parse(raw)
            return result if result else {
                "extracted_text": raw.strip(),
                "confidence": 0.5,
                "illegible_sections": [],
            }
        except Exception as e:
            logger.error(f"Handwriting OCR failed: {e}")
            return {"extracted_text": "", "confidence": 0.0, "error": str(e)}

    async def screen_literature(self, article_text: str) -> Dict[str, Any]:
        """Screen a published article for reportable patient safety cases."""
        prompt = LITERATURE_SCREENING_PROMPT.format(
            article_text=truncate_text(article_text, 8000)
        )
        try:
            raw = self._generate(prompt)
            result = safe_json_parse(raw)
            return result if result else {
                "contains_cases": False,
                "total_cases": 0,
                "cases": [],
            }
        except Exception as e:
            logger.error(f"Literature screening failed: {e}")
            return {"contains_cases": False, "total_cases": 0, "cases": [], "error": str(e)}


# Singleton instance
ai_service = AIService()
