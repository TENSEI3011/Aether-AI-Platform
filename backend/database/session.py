"""
============================================================
Database Session — SQLAlchemy engine and session factory
============================================================
Provides a reusable `get_db` dependency for FastAPI routes.
Uses SQLite for simplicity; swap DATABASE_URL for PostgreSQL
in production.
============================================================
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

# ── Engine & Session ──────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Declarative Base ──────────────────────────────────────
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session
    and ensures it is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
