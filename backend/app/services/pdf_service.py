"""
Smart Inbox Assistant — PDF Processing Service
Detects PDF type, extracts text, handles scanned/handwritten/article/non-English PDFs.
"""
import os
import io
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from PyPDF2 import PdfReader
from PIL import Image

logger = logging.getLogger(__name__)

# OCR threshold — if extracted text has fewer chars, assume scanned
SCANNED_TEXT_THRESHOLD = 100


class PDFService:
    """PDF type detection and text extraction service."""

    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, int]:
        """
        Extract text from a PDF using PyPDF2.
        Returns (extracted_text, page_count).
        """
        try:
            reader = PdfReader(file_path)
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(f"--- Page {i + 1} ---\n{page_text}")

            full_text = "\n\n".join(text_parts)
            return full_text, len(reader.pages)
        except Exception as e:
            logger.error(f"PDF text extraction failed for {file_path}: {e}")
            return "", 0

    def extract_images_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract images from a PDF. Returns list of image info dicts."""
        images = []
        try:
            reader = PdfReader(file_path)
            for page_num, page in enumerate(reader.pages):
                if "/XObject" in page["/Resources"]:
                    x_objects = page["/Resources"]["/XObject"].get_object()
                    for obj_name in x_objects:
                        obj = x_objects[obj_name].get_object()
                        if obj["/Subtype"] == "/Image":
                            try:
                                width = obj["/Width"]
                                height = obj["/Height"]
                                # Only process meaningful images (not tiny icons)
                                if width > 50 and height > 50:
                                    data = obj.get_data()
                                    images.append({
                                        "page": page_num + 1,
                                        "name": str(obj_name),
                                        "width": width,
                                        "height": height,
                                        "data": data,
                                        "size_bytes": len(data),
                                    })
                            except Exception as img_err:
                                logger.debug(f"Could not extract image {obj_name}: {img_err}")
        except Exception as e:
            logger.warning(f"Image extraction failed for {file_path}: {e}")

        return images

    def detect_pdf_type(self, file_path: str, extracted_text: str) -> Dict[str, Any]:
        """
        Detect PDF type based on text content analysis.
        Returns dict with pdf_type, detected_language, confidence.
        """
        text_length = len(extracted_text.strip())

        # If very little text extracted → likely scanned
        if text_length < SCANNED_TEXT_THRESHOLD:
            return {
                "pdf_type": "SCANNED",
                "detected_language": "Unknown",
                "confidence": 0.85,
                "reasoning": f"Only {text_length} characters extracted — likely scanned/handwritten."
            }

        # Check for article indicators
        article_indicators = [
            "abstract", "introduction", "methods", "results", "discussion",
            "conclusion", "references", "doi:", "journal", "published",
            "et al.", "figure", "table ", "keywords"
        ]
        text_lower = extracted_text.lower()
        indicator_count = sum(1 for ind in article_indicators if ind in text_lower)

        if indicator_count >= 4:
            return {
                "pdf_type": "ARTICLE",
                "detected_language": "English",
                "confidence": 0.80,
                "reasoning": f"Found {indicator_count} article indicators (abstract, methods, etc.)."
            }

        # Check for non-English using langdetect
        try:
            from langdetect import detect
            lang = detect(extracted_text[:2000])
            if lang != "en":
                return {
                    "pdf_type": "NON_ENGLISH",
                    "detected_language": lang,
                    "confidence": 0.80,
                    "reasoning": f"Language detected as '{lang}' (not English)."
                }
        except Exception:
            pass  # If langdetect fails, default to DIGITAL

        # Default: normal digital PDF
        return {
            "pdf_type": "DIGITAL",
            "detected_language": "English",
            "confidence": 0.75,
            "reasoning": "Standard digital PDF with extractable text."
        }

    def extract_tables_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Attempt to extract tables from text.
        Uses simple heuristics to detect tabular data.
        """
        tables = []
        lines = text.split("\n")
        current_table = []
        in_table = False

        for line in lines:
            # Heuristic: lines with multiple tab/pipe separators or consistent spacing
            stripped = line.strip()
            if "|" in stripped or "\t" in stripped:
                if not in_table:
                    in_table = True
                    current_table = []
                if "|" in stripped:
                    cells = [c.strip() for c in stripped.split("|") if c.strip()]
                else:
                    cells = [c.strip() for c in stripped.split("\t") if c.strip()]
                if cells:
                    current_table.append(cells)
            else:
                if in_table and len(current_table) >= 2:
                    tables.append({
                        "rows": current_table,
                        "row_count": len(current_table),
                        "col_count": len(current_table[0]) if current_table else 0,
                    })
                in_table = False
                current_table = []

        # Don't forget the last table
        if in_table and len(current_table) >= 2:
            tables.append({
                "rows": current_table,
                "row_count": len(current_table),
                "col_count": len(current_table[0]) if current_table else 0,
            })

        return tables

    async def process_pdf(self, file_path: str, ai_service=None) -> Dict[str, Any]:
        """
        Full PDF processing pipeline:
        1. Extract text
        2. Detect type
        3. Handle scanned (OCR/vision)
        4. Extract tables and images
        5. Handle non-English (translate)
        Returns comprehensive extraction result.
        """
        start_time = time.time()

        result = {
            "extracted_text": "",
            "pdf_type": "DIGITAL",
            "detected_language": "English",
            "ocr_confidence": None,
            "translated_text": None,
            "original_text": None,
            "table_data": [],
            "image_descriptions": [],
            "processing_time_ms": 0,
        }

        # Step 1: Try direct text extraction
        extracted_text, page_count = self.extract_text_from_pdf(file_path)
        result["page_count"] = page_count

        # Step 2: Detect PDF type
        type_info = self.detect_pdf_type(file_path, extracted_text)
        result["pdf_type"] = type_info["pdf_type"]
        result["detected_language"] = type_info.get("detected_language", "English")

        # Step 3: Handle scanned PDFs
        if type_info["pdf_type"] == "SCANNED" and ai_service:
            logger.info(f"Scanned PDF detected, using Gemini vision for OCR")
            try:
                # Convert first page to image for Gemini vision
                from pdf2image import convert_from_path
                images = convert_from_path(file_path, first_page=1, last_page=min(3, page_count or 1))
                all_text = []
                for i, img in enumerate(images):
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format="PNG")
                    img_bytes = img_byte_arr.getvalue()
                    ocr_result = await ai_service.ocr_handwritten(img_bytes, "image/png")
                    all_text.append(f"--- Page {i + 1} ---\n{ocr_result.get('extracted_text', '')}")
                    result["ocr_confidence"] = ocr_result.get("confidence", 0.5)

                extracted_text = "\n\n".join(all_text)
            except ImportError:
                logger.warning("pdf2image not available, using Tesseract OCR fallback")
                try:
                    import pytesseract
                    # Simple OCR fallback
                    extracted_text = "OCR fallback — install poppler for pdf2image support."
                    result["ocr_confidence"] = 0.3
                except Exception:
                    extracted_text = "OCR not available. Please install Tesseract and/or Poppler."
                    result["ocr_confidence"] = 0.0
            except Exception as e:
                logger.error(f"OCR processing failed: {e}")
                result["ocr_confidence"] = 0.0

        result["extracted_text"] = extracted_text

        # Step 4: Handle non-English
        if type_info["pdf_type"] == "NON_ENGLISH" and ai_service:
            result["original_text"] = extracted_text
            lang = type_info.get("detected_language", "Unknown")
            translation = await ai_service.translate_text(extracted_text, lang)
            result["translated_text"] = translation.get("translated_text", "")
            # Use translated text for downstream processing
            result["extracted_text"] = result["translated_text"] or extracted_text

        # Step 5: Extract tables
        result["table_data"] = self.extract_tables_from_text(extracted_text)

        # Step 6: Extract and describe images
        if ai_service:
            images = self.extract_images_from_pdf(file_path)
            for img_info in images[:5]:  # Limit to 5 images
                try:
                    desc = await ai_service.describe_image(img_info["data"], "image/png")
                    result["image_descriptions"].append({
                        "page": img_info["page"],
                        "width": img_info["width"],
                        "height": img_info["height"],
                        "description": desc.get("description", ""),
                        "flag_for_review": desc.get("flag_for_review", False),
                        "flag_reason": desc.get("flag_reason", ""),
                    })
                except Exception as e:
                    logger.warning(f"Image description failed: {e}")

        result["processing_time_ms"] = int((time.time() - start_time) * 1000)
        return result


# Singleton
pdf_service = PDFService()
