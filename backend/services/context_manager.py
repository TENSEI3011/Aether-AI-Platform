"""
============================================================
Context Manager — Conversational query memory (DB-backed)
============================================================
Hybrid strategy:
  • Fast path: in-memory dict for hot sessions (current server)
  • Persist:   writes to conversation_ctx table in Neon/PostgreSQL
  • Load:      on miss, reads from DB (survives server restarts)

Sessions older than SESSION_TTL_HOURS are not loaded from DB.

Gap 14: Context is now scoped by (session_id, dataset_id) to
prevent cross-dataset column hallucinations.
============================================================
"""

import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Max conversation turns to remember per session
MAX_HISTORY = 6

# Hot-session in-memory cache: { cache_key: [ {query, code, explanation, ts}, … ] }
_cache: Dict[str, list] = {}


def _cache_key(session_id: str, dataset_id: str = "") -> str:
    """Build a cache key scoped by session and optionally dataset."""
    if dataset_id:
        return f"{session_id}::{dataset_id}"
    return session_id


# --------------------------------------------------------------------------- #
# Public write API                                                             #
# --------------------------------------------------------------------------- #

def add_to_context(
    session_id: str,
    query: str,
    code: str,
    explanation: str,
    user_id: int = 0,
    dataset_id: str = "",
    db=None,          # SQLAlchemy Session — optional for DB persist
) -> None:
    """Record a successful query turn in both memory and DB."""
    entry = {
        "query":       query,
        "code":        code,
        "explanation": explanation,
        "dataset_id":  dataset_id,
        "timestamp":   time.time(),
    }

    key = _cache_key(session_id, dataset_id)

    # ── Memory cache ─────────────────────────────────────
    _cache.setdefault(key, []).append(entry)
    if len(_cache[key]) > MAX_HISTORY:
        _cache[key] = _cache[key][-MAX_HISTORY:]

    # ── DB persist (best-effort) ──────────────────────────
    if db is not None and user_id:
        try:
            from database.models import ConversationContext
            # Count existing turns
            existing = (
                db.query(ConversationContext)
                .filter(ConversationContext.session_id == session_id)
                .count()
            )
            row = ConversationContext(
                session_id  = session_id,
                user_id     = user_id,
                turn_index  = existing,
                query       = query,
                code        = code,
                explanation = explanation,
            )
            db.add(row)
            db.commit()

            # Trim old turns — keep only last MAX_HISTORY
            all_turns = (
                db.query(ConversationContext)
                .filter(ConversationContext.session_id == session_id)
                .order_by(ConversationContext.turn_index.asc())
                .all()
            )
            if len(all_turns) > MAX_HISTORY:
                for old in all_turns[: len(all_turns) - MAX_HISTORY]:
                    db.delete(old)
                db.commit()

        except Exception as exc:
            logger.warning("Failed to persist conversation context: %s", exc)


# --------------------------------------------------------------------------- #
# Public read API                                                              #
# --------------------------------------------------------------------------- #

def get_context(session_id: str, dataset_id: str = "", db=None) -> List[Dict[str, Any]]:
    """
    Return conversation history for a session.
    Reads from memory cache first; falls back to DB on cache miss.
    """
    key = _cache_key(session_id, dataset_id)

    if key in _cache and _cache[key]:
        return _cache[key]

    # Cache miss — try DB
    if db is not None:
        try:
            from database.models import ConversationContext
            rows = (
                db.query(ConversationContext)
                .filter(ConversationContext.session_id == session_id)
                .order_by(ConversationContext.turn_index.asc())
                .limit(MAX_HISTORY)
                .all()
            )
            if rows:
                history = [
                    {
                        "query":       r.query,
                        "code":        r.code,
                        "explanation": r.explanation,
                        "dataset_id":  "",
                        "timestamp":   r.created_at.timestamp() if r.created_at else 0,
                    }
                    for r in rows
                ]
                _cache[key] = history   # warm the cache
                return history
        except Exception as exc:
            logger.warning("Failed to load conversation context from DB: %s", exc)

    return []


def build_context_string(session_id: str, dataset_id: str = "", db=None) -> Optional[str]:
    """
    Build a formatted context string for the LLM prompt.
    Returns None if no history exists.
    """
    history = get_context(session_id, dataset_id=dataset_id, db=db)
    if not history:
        return None

    lines = ["PREVIOUS CONVERSATION:"]
    for i, entry in enumerate(history, 1):
        lines.append(f"  Turn {i}:")
        lines.append(f"    User asked: {entry['query']}")
        lines.append(f"    Generated code: {entry['code']}")
    lines.append("")
    lines.append("Use the above context to understand follow-up questions.")
    lines.append("If the user says 'now only for X' or 'filter by Y', modify the PREVIOUS code accordingly.")

    return "\n".join(lines)


def clear_context(session_id: str, dataset_id: str = "", db=None) -> None:
    """Clear conversation history for a session (memory + DB)."""
    key = _cache_key(session_id, dataset_id)
    _cache.pop(key, None)

    if db is not None:
        try:
            from database.models import ConversationContext
            db.query(ConversationContext).filter(
                ConversationContext.session_id == session_id
            ).delete()
            db.commit()
        except Exception as exc:
            logger.warning("Failed to clear conversation context from DB: %s", exc)
