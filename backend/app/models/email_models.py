"""
Smart Inbox Assistant — Pydantic Models for Email & Attachments
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class PDFType(str, Enum):
    DIGITAL = "DIGITAL"
    SCANNED = "SCANNED"
    ARTICLE = "ARTICLE"
    NON_ENGLISH = "NON_ENGLISH"


class AttachmentResponse(BaseModel):
    """Attachment data returned to the frontend."""
    attachment_id: int
    message_id: int
    filename: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    pdf_type: Optional[str] = None
    detected_language: Optional[str] = None
    ocr_confidence: Optional[float] = None
    extracted_text: Optional[str] = None
    translated_text: Optional[str] = None
    ai_summary: Optional[str] = None
    table_data: Optional[Any] = None
    image_descriptions: Optional[Any] = None
    processing_time_ms: Optional[int] = None


class EmailMessageResponse(BaseModel):
    """Email message data returned to the frontend."""
    message_id: int
    email_uid: Optional[str] = None
    sender: Optional[str] = None
    subject: Optional[str] = None
    received_date: Optional[datetime] = None
    body_text: Optional[str] = None
    processing_status: str = "PENDING"
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: Optional[datetime] = None
    attachments: List[AttachmentResponse] = []


class EmailListItem(BaseModel):
    """Compact email item for list view."""
    message_id: int
    sender: Optional[str] = None
    subject: Optional[str] = None
    received_date: Optional[datetime] = None
    processing_status: str = "PENDING"
    attachment_count: int = 0
    categories: List[str] = []
    max_confidence: Optional[float] = None


class FetchEmailsRequest(BaseModel):
    """Request to fetch emails from Gmail."""
    max_emails: int = Field(default=10, ge=1, le=50)


class FetchEmailsResponse(BaseModel):
    """Response after fetching emails."""
    fetched_count: int
    message: str
    message_ids: List[int] = []
