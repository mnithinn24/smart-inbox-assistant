"""
Smart Inbox Assistant — End-to-End Processing Pipeline
Orchestrates: PDF processing → AI classification → AI extraction → DB save → Audit log.
"""
import json
import logging
import time
from typing import Dict, Any, List
from app.database import execute_query, fetch_one, fetch_all
from app.services.ai_service import ai_service
from app.services.pdf_service import pdf_service

logger = logging.getLogger(__name__)


async def log_audit(
    message_id: int,
    action_type: str,
    performed_by: str,
    action_detail: Any = None,
    input_snapshot: str = None,
    output_snapshot: str = None,
):
    """Write an entry to the audit log."""
    await execute_query(
        """INSERT INTO audit_log (message_id, action_type, action_detail, performed_by, input_snapshot, output_snapshot)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (
            message_id,
            action_type,
            json.dumps(action_detail) if action_detail else None,
            performed_by,
            input_snapshot[:10000] if input_snapshot else None,
            output_snapshot[:10000] if output_snapshot else None,
        ),
    )


async def process_message(message_id: int):
    """
    Full processing pipeline for a single message.
    1. Update status to PROCESSING
    2. Process PDF attachments
    3. Classify the message
    4. Extract facts based on classification
    5. Generate summary
    6. Save everything to DB
    7. Update status to COMPLETED
    """
    start_time = time.time()
    logger.info(f"Starting pipeline for message {message_id}")

    try:
        # Update status
        await execute_query(
            "UPDATE inbox_messages SET processing_status = 'PROCESSING' WHERE message_id = %s",
            (message_id,),
        )

        # Fetch message
        message = await fetch_one(
            "SELECT * FROM inbox_messages WHERE message_id = %s", (message_id,)
        )
        if not message:
            raise Exception(f"Message {message_id} not found")

        subject = message.get("subject", "")
        sender = message.get("sender", "")
        body_text = message.get("body_text", "")

        # ── Step 1: Process PDF attachments ──
        attachments = await fetch_all(
            "SELECT * FROM attachments WHERE message_id = %s", (message_id,)
        )

        all_attachment_text = []
        for att in attachments:
            file_path = att.get("file_path", "")
            is_pdf = (att.get("content_type", "") == "application/pdf" or
                      (att.get("filename", "").lower().endswith(".pdf")))

            if is_pdf and file_path:
                logger.info(f"Processing PDF: {att.get('filename')}")
                pdf_result = await pdf_service.process_pdf(file_path, ai_service)

                # Update attachment in DB
                await execute_query(
                    """UPDATE attachments SET
                       pdf_type = %s,
                       detected_language = %s,
                       ocr_confidence = %s,
                       extracted_text = %s,
                       translated_text = %s,
                       original_text = %s,
                       table_data = %s,
                       image_descriptions = %s,
                       processing_time_ms = %s
                       WHERE attachment_id = %s""",
                    (
                        pdf_result.get("pdf_type"),
                        pdf_result.get("detected_language"),
                        pdf_result.get("ocr_confidence"),
                        pdf_result.get("extracted_text", ""),
                        pdf_result.get("translated_text"),
                        pdf_result.get("original_text"),
                        json.dumps(pdf_result.get("table_data", [])),
                        json.dumps(pdf_result.get("image_descriptions", [])),
                        pdf_result.get("processing_time_ms", 0),
                        att["attachment_id"],
                    ),
                )

                # Generate per-attachment summary
                att_summary = await ai_service.summarize_document(
                    subject, sender, body_text,
                    pdf_result.get("extracted_text", "")
                )
                await execute_query(
                    "UPDATE attachments SET ai_summary = %s WHERE attachment_id = %s",
                    (att_summary, att["attachment_id"]),
                )

                all_attachment_text.append(pdf_result.get("extracted_text", ""))

                await log_audit(
                    message_id, "PDF_PROCESSED", f"AI:{ai_service.model_name}",
                    {"filename": att.get("filename"), "pdf_type": pdf_result.get("pdf_type")},
                    input_snapshot=f"File: {att.get('filename')}",
                    output_snapshot=json.dumps({
                        "pdf_type": pdf_result.get("pdf_type"),
                        "text_length": len(pdf_result.get("extracted_text", "")),
                        "tables_found": len(pdf_result.get("table_data", [])),
                        "images_found": len(pdf_result.get("image_descriptions", [])),
                    }),
                )
            else:
                logger.info(f"Skipping non-PDF attachment: {att.get('filename')} ({att.get('content_type')})")
                await log_audit(
                    message_id, "ATTACHMENT_SKIPPED", "SYSTEM",
                    {"filename": att.get("filename"), "content_type": att.get("content_type")},
                )

        combined_attachment_text = "\n\n".join(all_attachment_text)

        # ── Step 2: Classify the message ──
        logger.info(f"Classifying message {message_id}...")
        classifications = await ai_service.classify_message(
            subject, sender, body_text, combined_attachment_text
        )

        categories = []
        for clf in classifications:
            category = clf.get("category", "NOT_RELEVANT")
            confidence = clf.get("confidence_score", 0.0)
            reason = clf.get("ai_reason", "")

            await execute_query(
                """INSERT INTO classifications
                   (message_id, category, confidence_score, ai_reason, reviewer_action)
                   VALUES (%s, %s, %s, %s, 'PENDING')""",
                (message_id, category, confidence, reason),
            )
            categories.append(category)

        await log_audit(
            message_id, "AI_CLASSIFY", f"AI:{ai_service.model_name}",
            classifications,
            input_snapshot=f"Subject: {subject}\nBody: {body_text[:500]}",
            output_snapshot=json.dumps(classifications),
        )

        # ── Step 3: Extract facts based on classification ──
        if "ICSR" in categories:
            logger.info(f"Extracting ICSR facts for message {message_id}...")
            icsr_data = await ai_service.extract_icsr(
                subject, sender, body_text, combined_attachment_text
            )
            if "error" not in icsr_data:
                await execute_query(
                    """INSERT INTO icsr_extractions
                       (message_id, patient_age, patient_sex, patient_weight, patient_height,
                        patient_history, reporter_name, reporter_role, reporter_country,
                        product_name, product_dose, product_route, product_start_date, product_stop_date,
                        reaction_description, reaction_onset_date, reaction_outcome,
                        is_serious, seriousness_criteria, ai_narrative,
                        field_confidence, source_references)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        message_id,
                        icsr_data.get("patient_age", "Not stated"),
                        icsr_data.get("patient_sex", "Not stated"),
                        icsr_data.get("patient_weight", "Not stated"),
                        icsr_data.get("patient_height", "Not stated"),
                        icsr_data.get("patient_history", "Not stated"),
                        icsr_data.get("reporter_name", "Not stated"),
                        icsr_data.get("reporter_role", "Not stated"),
                        icsr_data.get("reporter_country", "Not stated"),
                        icsr_data.get("product_name", "Not stated"),
                        icsr_data.get("product_dose", "Not stated"),
                        icsr_data.get("product_route", "Not stated"),
                        icsr_data.get("product_start_date", "Not stated"),
                        icsr_data.get("product_stop_date", "Not stated"),
                        icsr_data.get("reaction_description", "Not stated"),
                        icsr_data.get("reaction_onset_date", "Not stated"),
                        icsr_data.get("reaction_outcome", "Not stated"),
                        icsr_data.get("is_serious", "Unknown"),
                        icsr_data.get("seriousness_criteria", "Not stated"),
                        icsr_data.get("ai_narrative", ""),
                        json.dumps(icsr_data.get("field_confidence", {})),
                        json.dumps(icsr_data.get("source_references", {})),
                    ),
                )
                await log_audit(
                    message_id, "AI_EXTRACT_ICSR", f"AI:{ai_service.model_name}",
                    output_snapshot=json.dumps(icsr_data),
                )

        if "PQC" in categories:
            logger.info(f"Extracting PQC facts for message {message_id}...")
            pqc_data = await ai_service.extract_pqc(
                subject, sender, body_text, combined_attachment_text
            )
            if "error" not in pqc_data:
                await execute_query(
                    """INSERT INTO pqc_extractions
                       (message_id, product_name, batch_lot_number, complaint_description,
                        photo_mentioned, source_references, field_confidence)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        message_id,
                        pqc_data.get("product_name", "Not stated"),
                        pqc_data.get("batch_lot_number", "Not stated"),
                        pqc_data.get("complaint_description", "Not stated"),
                        pqc_data.get("photo_mentioned", "Unknown"),
                        json.dumps(pqc_data.get("source_references", {})),
                        json.dumps(pqc_data.get("field_confidence", {})),
                    ),
                )
                await log_audit(
                    message_id, "AI_EXTRACT_PQC", f"AI:{ai_service.model_name}",
                    output_snapshot=json.dumps(pqc_data),
                )

        if "MI" in categories:
            logger.info(f"Extracting MI facts for message {message_id}...")
            mi_data = await ai_service.extract_mi(
                subject, sender, body_text, combined_attachment_text
            )
            if "error" not in mi_data:
                await execute_query(
                    """INSERT INTO mi_extractions
                       (message_id, questions_asked, product_topic, source_references, field_confidence)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (
                        message_id,
                        json.dumps(mi_data.get("questions_asked", [])),
                        mi_data.get("product_topic", "Not stated"),
                        json.dumps(mi_data.get("source_references", {})),
                        json.dumps(mi_data.get("field_confidence", {})),
                    ),
                )
                await log_audit(
                    message_id, "AI_EXTRACT_MI", f"AI:{ai_service.model_name}",
                    output_snapshot=json.dumps(mi_data),
                )

        # ── Step 4: Update message status ──
        elapsed_ms = int((time.time() - start_time) * 1000)
        await execute_query(
            """UPDATE inbox_messages
               SET processing_status = 'COMPLETED', processing_time_ms = %s
               WHERE message_id = %s""",
            (elapsed_ms, message_id),
        )

        logger.info(f"Pipeline complete for message {message_id} in {elapsed_ms}ms")

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        logger.error(f"Pipeline failed for message {message_id}: {error_msg}")

        await execute_query(
            """UPDATE inbox_messages
               SET processing_status = 'ERROR', error_message = %s, processing_time_ms = %s
               WHERE message_id = %s""",
            (error_msg[:2000], elapsed_ms, message_id),
        )

        await log_audit(
            message_id, "PIPELINE_ERROR", "SYSTEM",
            {"error": error_msg},
        )
        raise
