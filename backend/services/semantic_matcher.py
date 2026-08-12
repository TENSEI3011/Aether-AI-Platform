"""
============================================================
Semantic Column Matcher — Finds the best matching column
for a user query using sentence embeddings + cosine similarity
============================================================
ML Concept: Text Embeddings + Cosine Similarity
Model: all-MiniLM-L6-v2 (~80MB, runs locally, no API needed)

Falls back to simple keyword matching if sentence-transformers
is not installed.
============================================================
"""

from __future__ import annotations
from typing import List, Optional, Dict, Tuple
import re
import logging

logger = logging.getLogger(__name__)

# ── Try to load sentence-transformers ────────────────────
try:
    from sentence_transformers import SentenceTransformer, util as st_util
    import torch
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False


# ── Singleton model (loaded once, reused across requests) ─
_model: Optional["SentenceTransformer"] = None
_model_name = "all-MiniLM-L6-v2"


def _get_model() -> Optional["SentenceTransformer"]:
    """Lazy-load the embedding model (only once per process)."""
    global _model
    if _model is None and _ST_AVAILABLE:
        try:
            logger.info("SemanticMatcher: Loading %s...", _model_name)
            _model = SentenceTransformer(_model_name)
            logger.info("SemanticMatcher: Model loaded successfully")
        except Exception as e:
            logger.warning("SemanticMatcher: Failed to load model: %s", e)
    return _model


# ─────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────

def find_best_column(
    query: str,
    column_names: List[str],
    threshold: float = 0.35,
) -> Optional[str]:
    """
    Find the most semantically similar column name for the user query.

    Parameters:
        query:        User's natural language query
        column_names: List of actual column names in the dataset
        threshold:    Minimum cosine similarity score to accept (0-1)

    Returns:
        Best matching column name, or None if no good match found.
    """
    if not column_names:
        return None

    model = _get_model()
    if model is not None:
        return _embedding_match(query, column_names, model, threshold)
    return _keyword_match(query, column_names)


def find_best_columns(
    query: str,
    column_names: List[str],
    top_k: int = 3,
    threshold: float = 0.3,
) -> List[Tuple[str, float]]:
    """
    Return top-K most relevant columns with their similarity scores.

    Returns:
        List of (column_name, score) tuples sorted by score descending.
    """
    if not column_names:
        return []

    model = _get_model()
    if model is None:
        return [(c, 0.5) for c in column_names[:top_k]]

    try:
        query_emb = model.encode(query, convert_to_tensor=True)
        # Humanise column names: "PM2.5_ugm3" → "PM2.5 ugm3"
        readable_cols = [_humanise(c) for c in column_names]
        col_embs = model.encode(readable_cols, convert_to_tensor=True)

        scores = st_util.cos_sim(query_emb, col_embs)[0]
        scored = sorted(
            zip(column_names, scores.tolist()),
            key=lambda x: x[1],
            reverse=True,
        )
        return [(name, score) for name, score in scored[:top_k] if score >= threshold]
    except Exception as e:
        logger.warning("SemanticMatcher: Scoring error: %s", e)
        return []


def enrich_schema_with_semantic_matches(
    query: str,
    schema_summary: str,
    column_names: List[str],
) -> str:
    """
    Prepend the most relevant columns to the schema summary
    so the LLM focuses on the right columns first.
    """
    top_cols = find_best_columns(query, column_names, top_k=5, threshold=0.3)
    if not top_cols:
        return schema_summary

    col_hint = "Most relevant columns for this query: " + ", ".join(
        f"'{name}' (score: {score:.2f})" for name, score in top_cols
    )
    return f"{col_hint}\n\n{schema_summary}"


# ─────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────

def _embedding_match(
    query: str,
    column_names: List[str],
    model: "SentenceTransformer",
    threshold: float,
) -> Optional[str]:
    """Use cosine similarity of embeddings to pick best column."""
    try:
        # Humanise column names for better matching
        readable_cols = [_humanise(c) for c in column_names]

        query_emb = model.encode(query, convert_to_tensor=True)
        col_embs = model.encode(readable_cols, convert_to_tensor=True)

        scores = st_util.cos_sim(query_emb, col_embs)[0]
        best_idx = int(scores.argmax())
        best_score = float(scores[best_idx])

        if best_score >= threshold:
            matched_col = column_names[best_idx]
            logger.debug(
                "SemanticMatcher: '%s' → '%s' (score=%.3f)",
                query, matched_col, best_score,
            )
            return matched_col
        return None
    except Exception as e:
        logger.warning("SemanticMatcher: Embedding match error: %s", e)
        return None


def _keyword_match(query: str, column_names: List[str]) -> Optional[str]:
    """Simple keyword fallback when embeddings are unavailable."""
    query_lower = query.lower()
    # Try longest match first to avoid partial matches
    for col in sorted(column_names, key=len, reverse=True):
        col_lower = col.lower()
        col_readable = _humanise(col).lower()
        if col_lower in query_lower or col_readable in query_lower:
            return col
    return None


def _humanise(column_name: str) -> str:
    """
    Convert raw column names to human-readable form for embedding.
    e.g. "PM2.5_ugm3" → "PM2.5 ugm3"
         "city_name"  → "city name"
         "AQI_Index"  → "AQI Index"
    """
    name = re.sub(r"[_\-\.]+", " ", column_name)
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)  # camelCase split
    return name.strip()
