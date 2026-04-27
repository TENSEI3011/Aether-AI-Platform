"""
============================================================
Database Session — SQLAlchemy engine and session factory
============================================================
Provides a reusable `get_db` dependency for FastAPI routes.
Supports both PostgreSQL (production) and SQLite (local dev).
The DATABASE_URL in .env controls which is used:
  - PostgreSQL: postgresql+psycopg2://user:pass@host/dbname
  - SQLite:     sqlite:///./database.db  (local dev fallback)
============================================================
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

# ── Detect database dialect ───────────────────────────────
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# ── Build connect_args & pool settings by dialect ─────────
if _is_sqlite:
    # SQLite requires this for multi-threaded FastAPI usage
    _connect_args = {"check_same_thread": False}
    _engine_kwargs = {}
else:
    # PostgreSQL — use connection pooling for stability
    # pool_pre_ping: test connection health before each use
    # (important for Render free tier which recycles DB connections)
    _connect_args = {}
    _engine_kwargs = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 300,  # Recycle connections every 5 min
    }

# ── Engine & Session ──────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    **_engine_kwargs,
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
