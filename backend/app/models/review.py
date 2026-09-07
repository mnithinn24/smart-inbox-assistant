"""
Smart Inbox Assistant — Pydantic Models for Review Queue
"""
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


class ReviewQueueItem(BaseModel):
    """A single item in the review queue."""
    message_id: int
    sender: Optional[str] = None
    subject: Optional[str] = None
    received_date: Optional[datetime] = None
    body_text_preview: Optional[str] = None
    processing_status: str = "PENDING"
    processing_time_ms: Optional[int] = None
    attachment_count: int = 0
    classifications: List[Dict[str, Any]] = []
    ai_summary: Optional[str] = None


class ReviewStats(BaseModel):
    """Dashboard statistics."""
    total_messages: int = 0
    pending_review: int = 0
    accepted: int = 0
    overridden: int = 0
    rejected: int = 0
    by_category: Dict[str, int] = {}
    avg_processing_time_ms: Optional[float] = None
    avg_confidence: Optional[float] = None


class AuditLogEntry(BaseModel):
    """A single audit log entry."""
    log_id: int
    message_id: Optional[int] = None
    action_type: str
    action_detail: Optional[Any] = None
    performed_by: Optional[str] = None
    timestamp: Optional[datetime] = None


class AuditLogResponse(BaseModel):
    """Paginated audit log."""
    entries: List[AuditLogEntry] = []
    total_count: int = 0
    page: int = 1
    page_size: int = 20
