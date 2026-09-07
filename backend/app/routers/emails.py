"""
Smart Inbox Assistant — Email Router
Endpoints for fetching, listing, and managing emails.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import fetch_one, fetch_all, execute_query
from app.models.email_models import (
    EmailMessageResponse, EmailListItem, FetchEmailsRequest,
    FetchEmailsResponse, AttachmentResponse,
)
from app.services.email_service import email_service
from app.services.queue_service import queue_service
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/emails", tags=["Emails"])


@router.post("/fetch", response_model=FetchEmailsResponse)
async def fetch_emails(request: FetchEmailsRequest):
    """Trigger a fetch of unread emails from Gmail IMAP."""
    try:
        message_ids = await email_service.fetch_emails(request.max_emails)

        # Queue each new message for processing
        for msg_id in message_ids:
            await queue_service.enqueue(msg_id)

        return FetchEmailsResponse(
            fetched_count=len(message_ids),
            message=f"Fetched {len(message_ids)} new emails and queued for processing.",
            message_ids=message_ids,
        )
    except Exception as e:
        logger.error(f"Email fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[EmailListItem])
async def list_emails(
    status: Optional[str] = Query(None, description="Filter by processing status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List all emails with compact info for the inbox view."""
    query = """
        SELECT m.message_id, m.sender, m.subject, m.received_date,
               m.processing_status,
               (SELECT COUNT(*) FROM attachments a WHERE a.message_id = m.message_id) as attachment_count
        FROM inbox_messages m
    """
    params = []
    if status:
        query += " WHERE m.processing_status = %s"
        params.append(status)
    query += " ORDER BY m.received_date DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    messages = await fetch_all(query, tuple(params))

    result = []
    for msg in messages:
        # Get classifications for this message
        classifications = await fetch_all(
            "SELECT category, confidence_score FROM classifications WHERE message_id = %s",
            (msg["message_id"],),
        )
        categories = [c["category"] for c in classifications]
        max_conf = max((c["confidence_score"] for c in classifications), default=None)

        result.append(EmailListItem(
            message_id=msg["message_id"],
            sender=msg.get("sender"),
            subject=msg.get("subject"),
            received_date=msg.get("received_date"),
            processing_status=msg.get("processing_status", "PENDING"),
            attachment_count=msg.get("attachment_count", 0),
            categories=categories,
            max_confidence=float(max_conf) if max_conf is not None else None,
        ))

    return result


@router.get("/{message_id}", response_model=EmailMessageResponse)
async def get_email(message_id: int):
    """Get full email details including body, attachments, and extractions."""
    message = await fetch_one(
        "SELECT * FROM inbox_messages WHERE message_id = %s", (message_id,)
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get attachments
    attachments_raw = await fetch_all(
        "SELECT * FROM attachments WHERE message_id = %s", (message_id,)
    )
    attachments = []
    for att in attachments_raw:
        attachments.append(AttachmentResponse(
            attachment_id=att["attachment_id"],
            message_id=att["message_id"],
            filename=att.get("filename"),
            content_type=att.get("content_type"),
            file_size=att.get("file_size"),
            pdf_type=att.get("pdf_type"),
            detected_language=att.get("detected_language"),
            ocr_confidence=float(att["ocr_confidence"]) if att.get("ocr_confidence") else None,
            extracted_text=att.get("extracted_text"),
            translated_text=att.get("translated_text"),
            ai_summary=att.get("ai_summary"),
            table_data=json.loads(att["table_data"]) if att.get("table_data") else None,
            image_descriptions=json.loads(att["image_descriptions"]) if att.get("image_descriptions") else None,
            processing_time_ms=att.get("processing_time_ms"),
        ))

    return EmailMessageResponse(
        message_id=message["message_id"],
        email_uid=message.get("email_uid"),
        sender=message.get("sender"),
        subject=message.get("subject"),
        received_date=message.get("received_date"),
        body_text=message.get("body_text"),
        processing_status=message.get("processing_status", "PENDING"),
        error_message=message.get("error_message"),
        processing_time_ms=message.get("processing_time_ms"),
        created_at=message.get("created_at"),
        attachments=attachments,
    )


@router.post("/{message_id}/process")
async def process_email(message_id: int):
    """Manually trigger processing for a specific email."""
    message = await fetch_one(
        "SELECT message_id FROM inbox_messages WHERE message_id = %s", (message_id,)
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Reset status and requeue
    await execute_query(
        "UPDATE inbox_messages SET processing_status = 'PENDING', error_message = NULL WHERE message_id = %s",
        (message_id,),
    )
    await queue_service.enqueue(message_id)
    return {"message": f"Message {message_id} queued for reprocessing."}
