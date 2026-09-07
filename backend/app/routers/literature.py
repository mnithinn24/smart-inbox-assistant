"""
Smart Inbox Assistant — Literature Screening Router (Bonus)
Endpoints for uploading article PDFs and screening for reportable patient cases.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from app.database import fetch_one, fetch_all, execute_query
from app.services.pdf_service import pdf_service
from app.services.ai_service import ai_service
from app.config import settings
import os
import json
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/literature", tags=["Literature Screening (Bonus)"])


@router.post("/upload")
async def upload_articles(files: List[UploadFile] = File(...)):
    """Upload a batch of article PDFs for literature screening."""
    results = []
    upload_dir = os.path.abspath(settings.upload_dir)
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            results.append({"filename": file.filename, "status": "skipped", "reason": "Not a PDF"})
            continue

        # Save file
        file_path = os.path.join(upload_dir, f"lit_{file.filename}")
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Create article record
        article_id = await execute_query(
            """INSERT INTO literature_articles (filename, file_path, processing_status)
               VALUES (%s, %s, 'PENDING')""",
            (file.filename, file_path),
        )

        results.append({
            "filename": file.filename,
            "article_id": article_id,
            "status": "queued",
        })

    # Process all queued articles in background
    for r in results:
        if r.get("status") == "queued":
            # Process immediately (could be queued in production)
            try:
                await _process_article(r["article_id"])
            except Exception as e:
                logger.error(f"Article processing failed: {e}")

    return {"uploaded": len(results), "articles": results}


async def _process_article(article_id: int):
    """Process a single article for literature screening."""
    start_time = time.time()

    await execute_query(
        "UPDATE literature_articles SET processing_status = 'PROCESSING' WHERE article_id = %s",
        (article_id,),
    )

    article = await fetch_one(
        "SELECT * FROM literature_articles WHERE article_id = %s", (article_id,)
    )
    if not article:
        return

    file_path = article["file_path"]

    # Extract text from PDF
    extracted_text, page_count = pdf_service.extract_text_from_pdf(file_path)

    await execute_query(
        "UPDATE literature_articles SET extracted_text = %s WHERE article_id = %s",
        (extracted_text, article_id),
    )

    # Screen for cases using AI
    screening_result = await ai_service.screen_literature(extracted_text)

    if screening_result.get("contains_cases") and screening_result.get("cases"):
        for case in screening_result["cases"]:
            await execute_query(
                """INSERT INTO literature_cases
                   (article_id, case_number, is_reportable, relevance_reason,
                    case_summary, patient_identifiable, confidence_score, source_location)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    article_id,
                    case.get("case_number", 1),
                    case.get("is_reportable", "No"),
                    case.get("relevance_reason", ""),
                    case.get("case_summary", ""),
                    case.get("patient_identifiable", "No"),
                    case.get("confidence_score", 0.0),
                    case.get("source_location", ""),
                ),
            )

    elapsed_ms = int((time.time() - start_time) * 1000)
    await execute_query(
        """UPDATE literature_articles
           SET processing_status = 'COMPLETED', processing_time_ms = %s
           WHERE article_id = %s""",
        (elapsed_ms, article_id),
    )

    logger.info(f"Article {article_id} processed in {elapsed_ms}ms, found {screening_result.get('total_cases', 0)} cases")


@router.get("")
async def list_articles():
    """List all uploaded articles with processing status."""
    articles = await fetch_all(
        """SELECT article_id, filename, processing_status, processing_time_ms, upload_timestamp
           FROM literature_articles ORDER BY upload_timestamp DESC"""
    )

    result = []
    for art in articles:
        # Count cases found
        case_count = await fetch_one(
            "SELECT COUNT(*) as cnt FROM literature_cases WHERE article_id = %s",
            (art["article_id"],),
        )
        result.append({
            **art,
            "cases_found": case_count["cnt"] if case_count else 0,
        })

    return result


@router.get("/{article_id}/cases")
async def get_article_cases(article_id: int):
    """Get identified cases for a specific article."""
    article = await fetch_one(
        "SELECT * FROM literature_articles WHERE article_id = %s", (article_id,)
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    cases = await fetch_all(
        """SELECT * FROM literature_cases WHERE article_id = %s ORDER BY case_number""",
        (article_id,),
    )

    return {
        "article": {
            "article_id": article["article_id"],
            "filename": article["filename"],
            "processing_status": article["processing_status"],
            "processing_time_ms": article.get("processing_time_ms"),
        },
        "cases": [
            {
                "case_id": c["case_id"],
                "case_number": c["case_number"],
                "is_reportable": c["is_reportable"],
                "relevance_reason": c.get("relevance_reason"),
                "case_summary": c.get("case_summary"),
                "patient_identifiable": c.get("patient_identifiable"),
                "confidence_score": float(c["confidence_score"]) if c.get("confidence_score") else 0,
                "source_location": c.get("source_location"),
            }
            for c in cases
        ],
    }
