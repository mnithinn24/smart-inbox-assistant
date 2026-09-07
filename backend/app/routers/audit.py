"""
Smart Inbox Assistant — Audit Log Router
Endpoints for viewing the audit trail.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import fetch_one, fetch_all
from app.models.review import AuditLogEntry, AuditLogResponse
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("", response_model=AuditLogResponse)
async def get_audit_log(
    message_id: Optional[int] = Query(None, description="Filter by message ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get paginated audit log with optional filters."""
    where_clauses = []
    params = []

    if message_id:
        where_clauses.append("message_id = %s")
        params.append(message_id)
    if action_type:
        where_clauses.append("action_type = %s")
        params.append(action_type)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Count total
    count_row = await fetch_one(
        f"SELECT COUNT(*) as cnt FROM audit_log WHERE {where_sql}", tuple(params)
    )
    total_count = count_row["cnt"] if count_row else 0

    # Fetch page
    offset = (page - 1) * page_size
    query_params = list(params) + [page_size, offset]
    rows = await fetch_all(
        f"""SELECT log_id, message_id, action_type, action_detail,
                   performed_by, timestamp
            FROM audit_log WHERE {where_sql}
            ORDER BY timestamp DESC LIMIT %s OFFSET %s""",
        tuple(query_params),
    )

    entries = []
    for row in rows:
        detail = row.get("action_detail")
        if isinstance(detail, str):
            try:
                detail = json.loads(detail)
            except json.JSONDecodeError:
                pass

        entries.append(AuditLogEntry(
            log_id=row["log_id"],
            message_id=row.get("message_id"),
            action_type=row["action_type"],
            action_detail=detail,
            performed_by=row.get("performed_by"),
            timestamp=row.get("timestamp"),
        ))

    return AuditLogResponse(
        entries=entries,
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.get("/{message_id}", response_model=list[AuditLogEntry])
async def get_message_audit(message_id: int):
    """Get full audit trail for a specific message."""
    rows = await fetch_all(
        """SELECT log_id, message_id, action_type, action_detail,
                  performed_by, timestamp
           FROM audit_log WHERE message_id = %s
           ORDER BY timestamp ASC""",
        (message_id,),
    )

    entries = []
    for row in rows:
        detail = row.get("action_detail")
        if isinstance(detail, str):
            try:
                detail = json.loads(detail)
            except json.JSONDecodeError:
                pass

        entries.append(AuditLogEntry(
            log_id=row["log_id"],
            message_id=row.get("message_id"),
            action_type=row["action_type"],
            action_detail=detail,
            performed_by=row.get("performed_by"),
            timestamp=row.get("timestamp"),
        ))

    return entries
