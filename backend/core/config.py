"""
============================================================
Core Configuration — Settings loaded from .env
============================================================
Uses pydantic-settings to parse environment variables.
All configurable values are centralised here.
============================================================
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application-wide settings sourced from environment variables."""

    # ── JWT Authentication ─────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Database ───────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./database.db"

    # ── LLM ────────────────────────────────────────────────
    LLM_MODEL_PATH: str = "microsoft/Phi-3-mini-4k-instruct"
    LLM_DEVICE: str = "cpu"
    GEMINI_API_KEY: str = ""  # Google Gemini API key (get free at aistudio.google.com)
    GEMINI_MODEL: str = "gemini-3.5-flash"  # Updated: gemini-2.0-flash was deprecated

    # ── Voice ──────────────────────────────────────────────
    WHISPER_MODEL: str = "base"

    # ── Server ─────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # ── File Upload ────────────────────────────────────────
    UPLOAD_DIR: str = "../datasets"
    MAX_FILE_SIZE_MB: int = 50

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"


# Singleton settings instance used across the application
settings = Settings()
