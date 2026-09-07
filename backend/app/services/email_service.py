"""
Smart Inbox Assistant — Email Service
Connects to Gmail IMAP, fetches unread emails, extracts metadata and PDF attachments.
"""
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import os
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings
from app.database import execute_query, fetch_one, fetch_all
from app.utils.helpers import clean_email_body

logger = logging.getLogger(__name__)


class EmailService:
    """Gmail IMAP email fetcher."""

    def __init__(self):
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self.upload_dir = os.path.abspath(settings.upload_dir)
        os.makedirs(self.upload_dir, exist_ok=True)

    def _decode_header_value(self, value: str) -> str:
        """Decode email header values (handles encoded subjects, sender names)."""
        if not value:
            return ""
        decoded_parts = decode_header(value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                result.append(str(part))
        return " ".join(result)

    def _extract_body(self, msg: email.message.Message) -> Tuple[str, str]:
        """Extract plain text and HTML body from an email message."""
        text_body = ""
        html_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        text_body = payload.decode(charset, errors="replace")
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        html_body = payload.decode(charset, errors="replace")
        else:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="replace")
                if content_type == "text/html":
                    html_body = decoded
                else:
                    text_body = decoded

        return clean_email_body(text_body), html_body

    def _extract_attachments(
        self, msg: email.message.Message, message_id: int
    ) -> List[Dict[str, Any]]:
        """Extract attachments from email, save PDFs to disk."""
        attachments = []

        if not msg.is_multipart():
            return attachments

        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" not in content_disposition:
                continue

            filename = part.get_filename()
            if filename:
                filename = self._decode_header_value(filename)
            else:
                filename = f"attachment_{len(attachments) + 1}"

            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)

            if payload:
                # Save file to disk
                safe_filename = f"{message_id}_{filename}"
                file_path = os.path.join(self.upload_dir, safe_filename)
                with open(file_path, "wb") as f:
                    f.write(payload)

                attachments.append({
                    "filename": filename,
                    "content_type": content_type,
                    "file_size": len(payload),
                    "file_path": file_path,
                    "is_pdf": content_type == "application/pdf" or filename.lower().endswith(".pdf"),
                })

                logger.info(f"Saved attachment: {filename} ({len(payload)} bytes)")

        return attachments

    async def fetch_emails(self, max_emails: int = 10) -> List[int]:
        """Fetch unread emails from Gmail IMAP. Returns list of new message_ids."""
        message_ids = []
        start_time = time.time()

        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(settings.gmail_user, settings.gmail_app_password)
            mail.select("INBOX")
            logger.info(f"Connected to Gmail IMAP as {settings.gmail_user}")

            # Search for unread emails
            status, data = mail.search(None, "UNSEEN")
            if status != "OK":
                logger.warning("No unread emails found")
                return []

            email_uids = data[0].split()
            if not email_uids:
                logger.info("No unread emails")
                return []

            # Process up to max_emails
            for uid in email_uids[:max_emails]:
                try:
                    uid_str = uid.decode()

                    # Check if already processed
                    existing = await fetch_one(
                        "SELECT message_id FROM inbox_messages WHERE email_uid = %s",
                        (uid_str,)
                    )
                    if existing:
                        logger.debug(f"Email UID {uid_str} already processed, skipping")
                        continue

                    # Fetch the email
                    status, msg_data = mail.fetch(uid, "(RFC822)")
                    if status != "OK":
                        continue

                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Extract metadata
                    sender = self._decode_header_value(msg.get("From", ""))
                    subject = self._decode_header_value(msg.get("Subject", ""))
                    date_str = msg.get("Date", "")

                    received_date = None
                    if date_str:
                        try:
                            received_date = parsedate_to_datetime(date_str)
                        except Exception:
                            received_date = None

                    # Extract body
                    text_body, html_body = self._extract_body(msg)

                    # Save to database
                    msg_id = await execute_query(
                        """INSERT INTO inbox_messages
                           (email_uid, sender, subject, received_date, body_text, body_html, processing_status)
                           VALUES (%s, %s, %s, %s, %s, %s, 'PENDING')""",
                        (uid_str, sender, subject, received_date, text_body, html_body)
                    )

                    # Extract and save attachments
                    attachments = self._extract_attachments(msg, msg_id)
                    for att in attachments:
                        await execute_query(
                            """INSERT INTO attachments
                               (message_id, filename, content_type, file_size, file_path)
                               VALUES (%s, %s, %s, %s, %s)""",
                            (msg_id, att["filename"], att["content_type"],
                             att["file_size"], att["file_path"])
                        )

                    message_ids.append(msg_id)
                    logger.info(f"Fetched email: {subject} (ID: {msg_id}, {len(attachments)} attachments)")

                except Exception as e:
                    logger.error(f"Error processing email UID {uid}: {e}")
                    continue

            mail.logout()
            elapsed = int((time.time() - start_time) * 1000)
            logger.info(f"Fetched {len(message_ids)} emails in {elapsed}ms")

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP connection error: {e}")
            raise Exception(f"Gmail IMAP connection failed: {str(e)}. Check credentials.")
        except Exception as e:
            logger.error(f"Email fetch error: {e}")
            raise

        return message_ids


# Singleton
email_service = EmailService()
