"""
Smart Inbox Assistant — Documents Router
Endpoints for PDF upload, document viewing, and extraction results.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from app.database import fetch_one, fetch_all, execute_query
from app.models.extraction import ExtractionSummary, ICSRExtractionResponse, PQCExtractionResponse, MIExtractionResponse
from app.services.queue_service import queue_service
import os
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF document for direct processing (non-email)."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Save the uploaded file
    upload_dir = os.path.abspath(settings.upload_dir)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, f"upload_{file.filename}")
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Create a synthetic email record for this uploaded document
    msg_id = await execute_query(
        """INSERT INTO inbox_messages
           (email_uid, sender, subject, body_text, processing_status)
           VALUES (%s, %s, %s, %s, 'PENDING')""",
        (f"upload_{file.filename}", "Direct Upload", f"Uploaded: {file.filename}",
         "Document uploaded directly for processing."),
    )

    # Create attachment record
    await execute_query(
        """INSERT INTO attachments
           (message_id, filename, content_type, file_size, file_path)
           VALUES (%s, %s, %s, %s, %s)""",
        (msg_id, file.filename, "application/pdf", len(content), file_path),
    )

    # Queue for processing
    await queue_service.enqueue(msg_id)

    return {
        "message": f"Document '{file.filename}' uploaded and queued for processing.",
        "message_id": msg_id,
    }


@router.get("/{message_id}/extraction", response_model=ExtractionSummary)
async def get_extraction(message_id: int):
    """Get all extraction results for a message."""
    message = await fetch_one(
        "SELECT message_id FROM inbox_messages WHERE message_id = %s", (message_id,)
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get categories
    classifications = await fetch_all(
        "SELECT category FROM classifications WHERE message_id = %s", (message_id,)
    )
    categories = [c["category"] for c in classifications]

    # Get ICSR extraction
    icsr = None
    icsr_row = await fetch_one(
        "SELECT * FROM icsr_extractions WHERE message_id = %s", (message_id,)
    )
    if icsr_row:
        icsr = ICSRExtractionResponse(
            extraction_id=icsr_row["extraction_id"],
            message_id=icsr_row["message_id"],
            patient_age=icsr_row.get("patient_age", "Not stated"),
            patient_sex=icsr_row.get("patient_sex", "Not stated"),
            patient_weight=icsr_row.get("patient_weight", "Not stated"),
            patient_height=icsr_row.get("patient_height", "Not stated"),
            patient_history=icsr_row.get("patient_history", "Not stated"),
            reporter_name=icsr_row.get("reporter_name", "Not stated"),
            reporter_role=icsr_row.get("reporter_role", "Not stated"),
            reporter_country=icsr_row.get("reporter_country", "Not stated"),
            product_name=icsr_row.get("product_name", "Not stated"),
            product_dose=icsr_row.get("product_dose", "Not stated"),
            product_route=icsr_row.get("product_route", "Not stated"),
            product_start_date=icsr_row.get("product_start_date", "Not stated"),
            product_stop_date=icsr_row.get("product_stop_date", "Not stated"),
            reaction_description=icsr_row.get("reaction_description", "Not stated"),
            reaction_onset_date=icsr_row.get("reaction_onset_date", "Not stated"),
            reaction_outcome=icsr_row.get("reaction_outcome", "Not stated"),
            is_serious=icsr_row.get("is_serious", "Unknown"),
            seriousness_criteria=icsr_row.get("seriousness_criteria", "Not stated"),
            ai_narrative=icsr_row.get("ai_narrative", ""),
            field_confidence=json.loads(icsr_row["field_confidence"]) if icsr_row.get("field_confidence") else {},
            source_references=json.loads(icsr_row["source_references"]) if icsr_row.get("source_references") else {},
            created_at=icsr_row.get("created_at"),
        )

    # Get PQC extraction
    pqc = None
    pqc_row = await fetch_one(
        "SELECT * FROM pqc_extractions WHERE message_id = %s", (message_id,)
    )
    if pqc_row:
        pqc = PQCExtractionResponse(
            extraction_id=pqc_row["extraction_id"],
            message_id=pqc_row["message_id"],
            product_name=pqc_row.get("product_name", "Not stated"),
            batch_lot_number=pqc_row.get("batch_lot_number", "Not stated"),
            complaint_description=pqc_row.get("complaint_description", "Not stated"),
            photo_mentioned=pqc_row.get("photo_mentioned", "Unknown"),
            source_references=json.loads(pqc_row["source_references"]) if pqc_row.get("source_references") else {},
            field_confidence=json.loads(pqc_row["field_confidence"]) if pqc_row.get("field_confidence") else {},
            created_at=pqc_row.get("created_at"),
        )

    # Get MI extraction
    mi = None
    mi_row = await fetch_one(
        "SELECT * FROM mi_extractions WHERE message_id = %s", (message_id,)
    )
    if mi_row:
        mi = MIExtractionResponse(
            extraction_id=mi_row["extraction_id"],
            message_id=mi_row["message_id"],
            questions_asked=json.loads(mi_row["questions_asked"]) if mi_row.get("questions_asked") else [],
            product_topic=mi_row.get("product_topic", "Not stated"),
            source_references=json.loads(mi_row["source_references"]) if mi_row.get("source_references") else {},
            field_confidence=json.loads(mi_row["field_confidence"]) if mi_row.get("field_confidence") else {},
            created_at=mi_row.get("created_at"),
        )

    return ExtractionSummary(
        message_id=message_id,
        categories=categories,
        icsr=icsr,
        pqc=pqc,
        mi=mi,
    )
