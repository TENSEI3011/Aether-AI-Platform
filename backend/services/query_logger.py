"""
============================================================
Query Logger — Logs all queries to the database
============================================================
"""

from sqlalchemy.orm import Session
from database.models import QueryLog


def log_query(
    db: Session,
    user_id: int,
    natural_query: str,
    generated_code: str = None,
    is_valid: bool = True,
    result_summary: str = None,
) -> QueryLog:
    """Save a query execution record to the database."""
    entry = QueryLog(
        user_id=user_id,
        natural_query=natural_query,
        generated_code=generated_code,
        is_valid=1 if is_valid else 0,
        result_summary=result_summary,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_user_history(db: Session, user_id: int, limit: int = 50):
    """Retrieve recent queries for a specific user."""
    return (
        db.query(QueryLog)
        .filter(QueryLog.user_id == user_id)
        .order_by(QueryLog.created_at.desc())
        .limit(limit)
        .all()
    )
