"""
Smart Inbox Assistant — Load Test Data into MySQL
Inserts synthetic test emails directly into the database and queues them for processing.
Run: py test-data/load_test_data.py
"""
import json
import os
import sys
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import settings
from app.database import init_db, close_db, execute_query


async def load_test_data():
    """Load test emails into the database."""
    test_file = os.path.join(os.path.dirname(__file__), "test_emails.json")

    if not os.path.exists(test_file):
        print("test_emails.json not found. Run generate_test_data.py first.")
        return

    with open(test_file, "r", encoding="utf-8") as f:
        emails = json.load(f)

    # Initialize DB
    await init_db()

    loaded = 0
    for email_data in emails:
        try:
            msg_id = await execute_query(
                """INSERT INTO inbox_messages
                   (email_uid, sender, subject, body_text, processing_status)
                   VALUES (%s, %s, %s, %s, 'PENDING')""",
                (
                    f"test_{email_data['id']}",
                    email_data.get("sender", "test@example.com"),
                    email_data.get("subject", "Test"),
                    email_data.get("body", ""),
                ),
            )
            loaded += 1
            print(f"  [{loaded}] Loaded: {email_data['subject'][:60]}")
        except Exception as e:
            print(f"  Error loading email {email_data['id']}: {e}")

    print(f"\nLoaded {loaded}/{len(emails)} test emails into MySQL.")
    print(f"Now use the API to process them:")
    print(f"  POST http://localhost:8000/api/emails/{{message_id}}/process")

    await close_db()


if __name__ == "__main__":
    asyncio.run(load_test_data())
