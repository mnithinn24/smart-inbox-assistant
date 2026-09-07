"""
Smart Inbox Assistant — OCR Service
Fallback OCR using pytesseract for scanned PDFs.
Primary OCR is done via Gemini Vision in ai_service.py.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OCRService:
    """Tesseract OCR service (fallback when Gemini Vision is unavailable)."""

    def __init__(self):
        self._tesseract_available = False
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
            logger.info("Tesseract OCR is available")
        except Exception:
            logger.warning(
                "Tesseract OCR is not available. "
                "Scanned PDF OCR will rely on Gemini Vision."
            )

    @property
    def is_available(self) -> bool:
        return self._tesseract_available

    def ocr_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Run OCR on an image using Tesseract."""
        if not self._tesseract_available:
            return {
                "text": "",
                "confidence": 0.0,
                "error": "Tesseract not installed"
            }

        try:
            import pytesseract
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(img)

            # Get confidence data
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return {
                "text": text.strip(),
                "confidence": round(avg_confidence / 100.0, 2),
                "word_count": len([w for w in data["text"] if w.strip()]),
            }
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return {"text": "", "confidence": 0.0, "error": str(e)}


# Singleton
ocr_service = OCRService()
