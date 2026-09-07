"""
Smart Inbox Assistant — FastAPI Application Entry Point
Main app with CORS, lifespan events, and router registration.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import init_db, close_db
from app.services.queue_service import queue_service
from app.services.pipeline import process_message
from app.routers import emails, review, documents, audit, literature
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("=" * 60)
    logger.info("Smart Inbox Assistant — Starting up")
    logger.info("=" * 60)

    # Initialize database pool
    await init_db()

    # Start background processing queue
    await queue_service.start_worker(process_message)

    logger.info(f"Gemini model: {settings.gemini_model}")
    logger.info(f"MySQL: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    logger.info(f"Upload dir: {os.path.abspath(settings.upload_dir)}")
    logger.info("Ready to process emails!")
    logger.info("=" * 60)

    yield  # App is running

    # Shutdown
    logger.info("Shutting down...")
    await queue_service.stop_worker()
    await close_db()
    logger.info("Shutdown complete.")


# Create FastAPI app
app = FastAPI(
    title="Smart Inbox Assistant",
    description=(
        "AI-powered email and document processing system for pharmaceutical safety. "
        "Reads incoming emails and PDFs, classifies them into 4 categories "
        "(Safety Report, Quality Complaint, Info Request, Not Relevant), "
        "extracts key facts, and provides a human review interface."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(emails.router)
app.include_router(review.router)
app.include_router(documents.router)
app.include_router(audit.router)
app.include_router(literature.router)

# Serve uploaded files
upload_dir = os.path.abspath(settings.upload_dir)
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "app": "Smart Inbox Assistant",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "ai_model": settings.gemini_model,
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    from app.database import pool
    return {
        "status": "healthy",
        "database": "connected" if pool and not pool._closed else "disconnected",
        "queue_size": queue_service.queue.qsize(),
        "queue_running": queue_service.is_running,
    }
