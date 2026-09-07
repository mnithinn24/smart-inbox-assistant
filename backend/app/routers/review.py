"""
Smart Inbox Assistant — Review Router
Endpoints for the human review queue: accept, override, stats.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import fetch_one, fetch_all, execute_query
from app.models.classification import AcceptRequest, OverrideRequest, RejectRequest, ClassificationResponse
from app.models.review import ReviewQueueItem, ReviewStats
from app.services.pipeline import log_audit
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/review", tags=["Review"])


@router.get("/queue", response_model=list[ReviewQueueItem])
async def get_review_queue(
    status: Optional[str] = Query(None, description="Filter: PENDING, ACCEPTED, OVERRIDDEN, REJECTED"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get the review queue — items awaiting human review."""
    query = """
        SELECT DISTINCT m.message_id, m.sender, m.subject, m.received_date,
               m.body_text, m.processing_status, m.processing_time_ms,
               (SELECT COUNT(*) FROM attachments a WHERE a.message_id = m.message_id) as attachment_count
        FROM inbox_messages m
        LEFT JOIN classifications c ON c.message_id = m.message_id
        WHERE m.processing_status = 'COMPLETED'
    """
    params = []

    if status:
        query += " AND c.reviewer_action = %s"
        params.append(status)
    if category:
        query += " AND c.category = %s"
        params.append(category)

    query += " ORDER BY m.received_date DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    messages = await fetch_all(query, tuple(params))

    result = []
    for msg in messages:
        # Get classifications
        classifications = await fetch_all(
            """SELECT classification_id, category, confidence_score, ai_reason,
                      reviewer_action, reviewer_override, reviewer_notes, reviewed_by, reviewed_at
               FROM classifications WHERE message_id = %s""",
            (msg["message_id"],),
        )

        clf_list = []
        for c in classifications:
            clf_list.append({
                "classification_id": c["classification_id"],
                "category": c["category"],
                "confidence_score": float(c["confidence_score"]) if c.get("confidence_score") else 0,
                "ai_reason": c.get("ai_reason", ""),
                "reviewer_action": c.get("reviewer_action", "PENDING"),
                "reviewer_override": c.get("reviewer_override"),
                "reviewer_notes": c.get("reviewer_notes"),
                "reviewed_by": c.get("reviewed_by"),
                "reviewed_at": str(c["reviewed_at"]) if c.get("reviewed_at") else None,
            })

        # Get AI summary from first attachment
        att_summary = await fetch_one(
            "SELECT ai_summary FROM attachments WHERE message_id = %s AND ai_summary IS NOT NULL LIMIT 1",
            (msg["message_id"],),
        )

        body_preview = (msg.get("body_text", "") or "")[:300]

        result.append(ReviewQueueItem(
            message_id=msg["message_id"],
            sender=msg.get("sender"),
            subject=msg.get("subject"),
            received_date=msg.get("received_date"),
            body_text_preview=body_preview if body_preview else None,
            processing_status=msg.get("processing_status", "PENDING"),
            processing_time_ms=msg.get("processing_time_ms"),
            attachment_count=msg.get("attachment_count", 0),
            classifications=clf_list,
            ai_summary=att_summary["ai_summary"] if att_summary else None,
        ))

    return result


@router.get("/stats", response_model=ReviewStats)
async def get_review_stats():
    """Get dashboard statistics."""
    total = await fetch_one("SELECT COUNT(*) as cnt FROM inbox_messages")
    pending = await fetch_one(
        "SELECT COUNT(DISTINCT message_id) as cnt FROM classifications WHERE reviewer_action = 'PENDING'"
    )
    accepted = await fetch_one(
        "SELECT COUNT(DISTINCT message_id) as cnt FROM classifications WHERE reviewer_action = 'ACCEPTED'"
    )
    overridden = await fetch_one(
        "SELECT COUNT(DISTINCT message_id) as cnt FROM classifications WHERE reviewer_action = 'OVERRIDDEN'"
    )
    rejected = await fetch_one(
        "SELECT COUNT(DISTINCT message_id) as cnt FROM classifications WHERE reviewer_action = 'REJECTED'"
    )

    # Count by category
    cats = await fetch_all(
        "SELECT category, COUNT(*) as cnt FROM classifications GROUP BY category"
    )
    by_category = {c["category"]: c["cnt"] for c in cats}

    # Average processing time
    avg_time = await fetch_one(
        "SELECT AVG(processing_time_ms) as avg_ms FROM inbox_messages WHERE processing_status = 'COMPLETED'"
    )
    avg_conf = await fetch_one(
        "SELECT AVG(confidence_score) as avg_conf FROM classifications"
    )

    return ReviewStats(
        total_messages=total["cnt"] if total else 0,
        pending_review=pending["cnt"] if pending else 0,
        accepted=accepted["cnt"] if accepted else 0,
        overridden=overridden["cnt"] if overridden else 0,
        rejected=rejected["cnt"] if rejected else 0,
        by_category=by_category,
        avg_processing_time_ms=float(avg_time["avg_ms"]) if avg_time and avg_time["avg_ms"] else None,
        avg_confidence=float(avg_conf["avg_conf"]) if avg_conf and avg_conf["avg_conf"] else None,
    )


@router.post("/{classification_id}/accept")
async def accept_classification(classification_id: int, request: AcceptRequest):
    """Accept the AI's classification."""
    clf = await fetch_one(
        "SELECT * FROM classifications WHERE classification_id = %s", (classification_id,)
    )
    if not clf:
        raise HTTPException(status_code=404, detail="Classification not found")

    await execute_query(
        """UPDATE classifications
           SET reviewer_action = 'ACCEPTED', reviewed_by = %s, reviewer_notes = %s, reviewed_at = NOW()
           WHERE classification_id = %s""",
        (request.reviewed_by, request.notes, classification_id),
    )

    await log_audit(
        clf["message_id"], "REVIEWER_ACCEPT", request.reviewed_by,
        {"classification_id": classification_id, "category": clf["category"]},
    )

    return {"message": f"Classification {classification_id} accepted."}


@router.post("/{classification_id}/override")
async def override_classification(classification_id: int, request: OverrideRequest):
    """Override the AI's classification with a new category."""
    clf = await fetch_one(
        "SELECT * FROM classifications WHERE classification_id = %s", (classification_id,)
    )
    if not clf:
        raise HTTPException(status_code=404, detail="Classification not found")

    await execute_query(
        """UPDATE classifications
           SET reviewer_action = 'OVERRIDDEN', reviewer_override = %s,
               reviewed_by = %s, reviewer_notes = %s, reviewed_at = NOW()
           WHERE classification_id = %s""",
        (request.new_category.value, request.reviewed_by, request.notes, classification_id),
    )

    await log_audit(
        clf["message_id"], "REVIEWER_OVERRIDE", request.reviewed_by,
        {
            "classification_id": classification_id,
            "original_category": clf["category"],
            "new_category": request.new_category.value,
            "notes": request.notes,
        },
    )

    return {"message": f"Classification {classification_id} overridden to {request.new_category.value}."}


@router.post("/{classification_id}/reject")
async def reject_classification(classification_id: int, request: RejectRequest):
    """Reject the AI's classification (spam, duplicate, or AI error)."""
    clf = await fetch_one(
        "SELECT * FROM classifications WHERE classification_id = %s", (classification_id,)
    )
    if not clf:
        raise HTTPException(status_code=404, detail="Classification not found")

    await execute_query(
        """UPDATE classifications
           SET reviewer_action = 'REJECTED', reviewed_by = %s, reviewer_notes = %s, reviewed_at = NOW()
           WHERE classification_id = %s""",
        (request.reviewed_by, request.reason, classification_id),
    )

    await log_audit(
        clf["message_id"], "REVIEWER_REJECT", request.reviewed_by,
        {
            "classification_id": classification_id,
            "category": clf["category"],
            "reason": request.reason,
        },
    )

    return {"message": f"Classification {classification_id} rejected."}
