"""
============================================================
Core Configuration — Settings loaded from .env
============================================================
Uses pydantic-settings to parse environment variables.
All configurable values are centralised here.
============================================================
"""

import secrets
import logging
from pydantic_settings import BaseSettings
from pathlib import Path

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application-wide settings sourced from environment variables."""

    # ── JWT Authentication ─────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080   # 7 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120      # 2 hours

    # ── Database ───────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./database.db"

    # ── LLM — Google Gemini ───────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"


    # ── Server ─────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # ── File Upload ────────────────────────────────────────
    UPLOAD_DIR: str = "../datasets"
    MAX_FILE_SIZE_MB: int = 50

    # ── SMTP Email (for Scheduled Reports & Alerts) ───────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton settings instance used across the application
settings = Settings()

# ── Safety: auto-generate a real secret if default is present ──
if settings.SECRET_KEY == "change-me-in-production":
    _generated = secrets.token_urlsafe(48)
    settings.SECRET_KEY = _generated
    logger.warning(
        "SECRET_KEY was not set — auto-generated a random key for this session. "
        "Set SECRET_KEY in .env for persistent sessions across restarts."
    )
