"""
Smart Inbox Assistant — Pydantic Models for Classification
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CategoryType(str, Enum):
    ICSR = "ICSR"
    PQC = "PQC"
    MI = "MI"
    NOT_RELEVANT = "NOT_RELEVANT"


class ReviewerAction(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    OVERRIDDEN = "OVERRIDDEN"
    REJECTED = "REJECTED"


class ClassificationResult(BaseModel):
    """AI classification result for a single category."""
    category: CategoryType
    confidence_score: float = Field(ge=0.0, le=1.0)
    ai_reason: str


class ClassificationResponse(BaseModel):
    """Classification data returned to the frontend."""
    classification_id: int
    message_id: int
    category: str
    confidence_score: float
    ai_reason: Optional[str] = None
    reviewer_action: str = "PENDING"
    reviewer_override: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class ClassifyRequest(BaseModel):
    """Request to classify a message."""
    message_id: int


class AcceptRequest(BaseModel):
    """Accept AI classification."""
    reviewed_by: str = "reviewer"
    notes: Optional[str] = None


class OverrideRequest(BaseModel):
    """Override AI classification."""
    new_category: CategoryType
    reviewed_by: str = "reviewer"
    notes: Optional[str] = None


class RejectRequest(BaseModel):
    """Reject AI classification (spam, duplicate, or AI error)."""
    reviewed_by: str = "reviewer"
    reason: Optional[str] = None

