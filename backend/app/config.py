"""
Smart Inbox Assistant — Application Configuration
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Gmail IMAP
    gmail_user: str = ""
    gmail_app_password: str = ""

    # Google Gemini Pro
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # MySQL Database
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "Nithin@9999"
    db_name: str = "smart_inbox"

    # App Settings
    upload_dir: str = "../uploads"
    poll_interval_seconds: int = 120
    max_workers: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
