"""
Smart Inbox Assistant — Pydantic Models for Fact Extraction
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ICSRExtraction(BaseModel):
    """Individual Case Safety Report (adverse drug reaction) extracted facts."""
    # Patient
    patient_age: str = "Not stated"
    patient_sex: str = "Not stated"
    patient_weight: str = "Not stated"
    patient_height: str = "Not stated"
    patient_history: str = "Not stated"
    # Reporter
    reporter_name: str = "Not stated"
    reporter_role: str = "Not stated"
    reporter_country: str = "Not stated"
    # Product
    product_name: str = "Not stated"
    product_dose: str = "Not stated"
    product_route: str = "Not stated"
    product_start_date: str = "Not stated"
    product_stop_date: str = "Not stated"
    # Reaction
    reaction_description: str = "Not stated"
    reaction_onset_date: str = "Not stated"
    reaction_outcome: str = "Not stated"
    # Severity
    is_serious: str = "Unknown"
    seriousness_criteria: str = "Not stated"
    # Narrative
    ai_narrative: str = ""
    # Confidence per field
    field_confidence: Dict[str, float] = {}
    # Source traceability
    source_references: Dict[str, Any] = {}


class ICSRExtractionResponse(ICSRExtraction):
    """ICSR extraction with database ID."""
    extraction_id: int
    message_id: int
    created_at: Optional[datetime] = None


class PQCExtraction(BaseModel):
    """Product Quality Complaint extracted facts."""
    product_name: str = "Not stated"
    batch_lot_number: str = "Not stated"
    complaint_description: str = "Not stated"
    photo_mentioned: str = "Unknown"
    source_references: Dict[str, Any] = {}
    field_confidence: Dict[str, float] = {}


class PQCExtractionResponse(PQCExtraction):
    """PQC extraction with database ID."""
    extraction_id: int
    message_id: int
    created_at: Optional[datetime] = None


class MIExtraction(BaseModel):
    """Medical Information Request extracted facts."""
    questions_asked: List[str] = []
    product_topic: str = "Not stated"
    source_references: Dict[str, Any] = {}
    field_confidence: Dict[str, float] = {}


class MIExtractionResponse(MIExtraction):
    """MI extraction with database ID."""
    extraction_id: int
    message_id: int
    created_at: Optional[datetime] = None


class ExtractionSummary(BaseModel):
    """Combined extraction results for a message."""
    message_id: int
    categories: List[str] = []
    icsr: Optional[ICSRExtractionResponse] = None
    pqc: Optional[PQCExtractionResponse] = None
    mi: Optional[MIExtractionResponse] = None
