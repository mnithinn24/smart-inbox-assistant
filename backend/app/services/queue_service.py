"""
Smart Inbox Assistant — Background Task Queue Service
Uses asyncio.Queue for processing items asynchronously.
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, Awaitable
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class QueueService:
    """Async background task queue for document processing."""

    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.tasks: Dict[int, Dict[str, Any]] = {}  # message_id → status info
        self.worker_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def start_worker(self, processor: Callable[[int], Awaitable[None]]):
        """Start the background worker that processes queued items."""
        self.is_running = True
        self.processor = processor
        self.worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Queue worker started")

    async def stop_worker(self):
        """Stop the background worker."""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Queue worker stopped")

    async def enqueue(self, message_id: int):
        """Add a message to the processing queue."""
        self.tasks[message_id] = {
            "status": TaskStatus.QUEUED,
            "queued_at": time.time(),
            "started_at": None,
            "completed_at": None,
            "error": None,
        }
        await self.queue.put(message_id)
        logger.info(f"Message {message_id} added to processing queue (queue size: {self.queue.qsize()})")

    def get_status(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Get the processing status of a message."""
        return self.tasks.get(message_id)

    async def _worker_loop(self):
        """Main worker loop — processes items from the queue sequentially."""
        logger.info("Worker loop started, waiting for items...")
        while self.is_running:
            try:
                message_id = await asyncio.wait_for(self.queue.get(), timeout=5.0)

                self.tasks[message_id]["status"] = TaskStatus.PROCESSING
                self.tasks[message_id]["started_at"] = time.time()
                logger.info(f"Processing message {message_id}...")

                try:
                    await self.processor(message_id)
                    self.tasks[message_id]["status"] = TaskStatus.COMPLETED
                    self.tasks[message_id]["completed_at"] = time.time()
                    elapsed = self.tasks[message_id]["completed_at"] - self.tasks[message_id]["started_at"]
                    logger.info(f"Message {message_id} processed in {elapsed:.1f}s")
                except Exception as e:
                    self.tasks[message_id]["status"] = TaskStatus.ERROR
                    self.tasks[message_id]["error"] = str(e)
                    logger.error(f"Error processing message {message_id}: {e}")

                self.queue.task_done()

            except asyncio.TimeoutError:
                continue  # No items in queue, check if still running
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)


# Singleton
queue_service = QueueService()
