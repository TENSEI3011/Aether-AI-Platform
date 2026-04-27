"""
============================================================
Database Models — SQLAlchemy ORM models
============================================================
Tables:
  - users             → Registered user accounts
  - query_logs        → Every query executed by a user
  - conversation_ctx  → DB-backed conversational session memory
  - dataset_records   → Metadata for every uploaded dataset
============================================================
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.sql import func

from database.session import Base


class User(Base):
    """Registered user account."""
    __tablename__ = "users"

    id             = Column(Integer, primary_key=True, index=True)
    username       = Column(String(50), unique=True, nullable=False, index=True)
    email          = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at     = Column(DateTime, server_default=func.now())


class QueryLog(Base):
    """Log of every query executed by a user."""
    __tablename__ = "query_logs"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    natural_query  = Column(Text, nullable=False)
    generated_code = Column(Text, nullable=True)
    is_valid       = Column(Integer, default=1)
    result_summary = Column(Text, nullable=True)
    chart_type     = Column(String(30), nullable=True)   # bar/line/pie/scatter/…
    created_at     = Column(DateTime, server_default=func.now())


class ConversationContext(Base):
    """
    Persistent conversational session memory.
    One row per (session_id, turn). Replaces the volatile in-memory dict
    so conversation context survives server restarts.
    """
    __tablename__ = "conversation_ctx"

    id          = Column(Integer, primary_key=True, index=True)
    session_id  = Column(String(128), nullable=False, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    turn_index  = Column(Integer, nullable=False, default=0)
    query       = Column(Text, nullable=False)
    code        = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    created_at  = Column(DateTime, server_default=func.now())


class DatasetRecord(Base):
    """
    Metadata for every dataset uploaded by a user.
    Allows users to list and re-use past uploads without
    re-uploading the file.
    """
    __tablename__ = "dataset_records"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    dataset_id     = Column(String(64), nullable=False, unique=True, index=True)
    filename       = Column(String(255), nullable=False)
    filepath       = Column(Text, nullable=False)
    row_count      = Column(Integer, nullable=True)
    column_count   = Column(Integer, nullable=True)
    schema_summary = Column(Text, nullable=True)
    uploaded_at    = Column(DateTime, server_default=func.now())
    is_active      = Column(Boolean, default=True)   # False = deleted/expired


class SavedQuery(Base):
    """Saved query template for one-click re-use."""
    __tablename__ = "saved_queries"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name           = Column(String(100), nullable=False)
    dataset_id     = Column(String(64), nullable=False)
    natural_query  = Column(Text, nullable=False)
    graph_type     = Column(String(30), default="auto")
    created_at     = Column(DateTime, server_default=func.now())


class ScheduledReport(Base):
    """Scheduled automatic report generation and delivery."""
    __tablename__ = "scheduled_reports"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    dataset_id      = Column(String(64), nullable=False)
    query           = Column(Text, nullable=False)
    frequency       = Column(String(20), nullable=False, default="daily")  # daily/weekly/monthly
    email           = Column(String(255), nullable=True)
    is_active       = Column(Boolean, default=True)
    last_run        = Column(DateTime, nullable=True)
    created_at      = Column(DateTime, server_default=func.now())


class SmartAlert(Base):
    """Alert rule that triggers when data meets a condition."""
    __tablename__ = "smart_alerts"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    dataset_id      = Column(String(64), nullable=False)
    column_name     = Column(String(100), nullable=False)
    condition       = Column(String(10), nullable=False)   # gt, lt, eq, gte, lte
    threshold       = Column(Float, nullable=False)
    label           = Column(String(150), nullable=True)    # user-friendly label
    is_active       = Column(Boolean, default=True)
    last_triggered  = Column(DateTime, nullable=True)
    created_at      = Column(DateTime, server_default=func.now())


class AlertNotification(Base):
    """Notification generated when an alert rule fires."""
    __tablename__ = "alert_notifications"

    id          = Column(Integer, primary_key=True, index=True)
    alert_id    = Column(Integer, ForeignKey("smart_alerts.id"), nullable=False)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message     = Column(Text, nullable=False)
    is_read     = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())
