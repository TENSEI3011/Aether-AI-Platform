"""
============================================================
Database Models — SQLAlchemy ORM models
============================================================
Defines the User and QueryLog tables.
============================================================
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from database.session import Base


class User(Base):
    """Registered user account."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class QueryLog(Base):
    """Log of every query executed by a user."""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    natural_query = Column(Text, nullable=False)           # Original NL query
    generated_code = Column(Text, nullable=True)            # Pandas code from LLM
    is_valid = Column(Integer, default=1)                   # 1 = passed validation
    result_summary = Column(Text, nullable=True)            # JSON string of result
    created_at = Column(DateTime, server_default=func.now())
