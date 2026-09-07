"""
Smart Inbox Assistant — Utility Helpers
"""
import json
import logging
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def safe_json_parse(text: str) -> Optional[Any]:
    """Safely parse JSON from AI responses, handling markdown code blocks and whitespace."""
    if not text:
        return None

    cleaned = text.strip()

    # Strip markdown code blocks if present (```json ... ``` or ``` ... ```)
    for prefix in ["```json", "```JSON", "```"]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find the outermost JSON object { ... }
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(cleaned[start:end])
        except json.JSONDecodeError:
            pass

    # Try to find a JSON array [ ... ]
    start = cleaned.find("[")
    end = cleaned.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(cleaned[start:end])
        except json.JSONDecodeError:
            pass

    logger.warning(f"safe_json_parse: could not parse JSON from: {text[:300]}")
    return None



def truncate_text(text: str, max_chars: int = 5000) -> str:
    """Truncate text to a maximum number of characters."""
    if not text or len(text) <= max_chars:
        return text or ""
    return text[:max_chars] + f"\n\n[...truncated, {len(text) - max_chars} more characters...]"


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime for display."""
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def clean_email_body(text: str) -> str:
    """Clean up email body text — remove excessive whitespace and signatures."""
    if not text:
        return ""
    # Remove excessive blank lines
    lines = text.split("\n")
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append("")
        else:
            blank_count = 0
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()
