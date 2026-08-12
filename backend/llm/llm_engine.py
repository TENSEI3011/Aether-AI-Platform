"""
============================================================
LLM Engine — Generates Pandas code from natural language
============================================================
PRIMARY:  Google Gemini 3.5 Flash (free tier)
FALLBACK: Keyword-matching stub (when no API key is set)

ENHANCEMENTS ADDED:
  ✅ Conversation Memory (Multi-turn ICL) — last N Q&A pairs
     are injected into the prompt for context-aware queries.
  ✅ Semantic Column Matching — uses MiniLM embeddings to
     find the closest column even if the name doesn't match.
  ✅ Self-Correction Retry — on code failure, the error is
     fed back to Gemini to get a corrected version (up to 3x).

Set GEMINI_API_KEY in your .env to enable real AI.
Get a free key at: https://aistudio.google.com/apikey

IMPORTANT:
  - The LLM ONLY generates code strings
  - It NEVER executes code
  - All output passes through the validation layer
============================================================
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional
from collections import deque

logger = logging.getLogger(__name__)

# -- Use the new google.genai SDK (replaces deprecated google.generativeai) --
try:
    from google import genai
    from google.genai import types as genai_types
    _GEMINI_SDK_AVAILABLE = True
except ImportError:
    _GEMINI_SDK_AVAILABLE = False

# -- Semantic matching (optional, enhances column resolution) --
try:
    from services.semantic_matcher import enrich_schema_with_semantic_matches
    _SEMANTIC_AVAILABLE = True
except ImportError:
    _SEMANTIC_AVAILABLE = False

from core.config import settings


# ── Conversation History Entry ────────────────────────────
class ConversationTurn:
    """Represents one round of Q&A in a conversation."""
    def __init__(self, query: str, code: str, explanation: str):
        self.query = query
        self.code = code
        self.explanation = explanation

    def to_prompt_str(self) -> str:
        """Serialize this turn to a human-readable string for LLM prompt injection."""
        return f"User asked: \"{self.query}\"\nGenerated: {self.code}"


class LLMEngine:
    """
    LLM integration for natural-language to Pandas code generation.

    Uses Google Gemini 3.5 Flash when GEMINI_API_KEY is set in .env.
    Falls back to keyword-matching stub when no key is available.

    Supports conversation memory (ICL) and self-correction.
    """

    def __init__(self, memory_size: int = 5):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.use_gemini = _GEMINI_SDK_AVAILABLE and bool(self.api_key)
        self.is_stub = not self.use_gemini

        # ── Conversation Memory ───────────────────────────
        # Stores the last `memory_size` Q&A turns per session.
        # keyed by session_id (user_id or dataset_id)
        self._memory: Dict[str, deque] = {}
        self._memory_size = memory_size

        if self.use_gemini:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("LLMEngine: %s loaded — real AI active", settings.GEMINI_MODEL)
            if _SEMANTIC_AVAILABLE:
                logger.info("LLMEngine: Semantic column matching enabled")
        else:
            self.client = None
            if not _GEMINI_SDK_AVAILABLE:
                logger.warning("LLMEngine: google-genai not installed — using stub")
            else:
                logger.warning("LLMEngine: GEMINI_API_KEY not set — using stub fallback")

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def generate_code(
        self,
        natural_query: str,
        schema_summary: str,
        column_names: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convert a natural language query into Pandas code.

        Parameters:
            natural_query: The user question
            schema_summary: Schema context string from schema_extractor
            column_names:   List of actual column names (for semantic matching)
            session_id:     User/dataset ID for conversation memory

        Returns:
            {
                "code": str,         # Generated Pandas code
                "confidence": float, # 0.0-1.0
                "explanation": str,  # Human-readable explanation
                "engine": str        # "gemini-3.5-flash" or "keyword-stub"
            }
        """
        # ── Semantic schema enrichment ────────────────────
        enriched_schema = schema_summary
        if _SEMANTIC_AVAILABLE and column_names:
            try:
                enriched_schema = enrich_schema_with_semantic_matches(
                    natural_query, schema_summary, column_names
                )
            except Exception as e:
                logger.warning("LLMEngine: Semantic enrichment failed: %s", e)

        if self.use_gemini:
            result = self._gemini_generate(
                natural_query, enriched_schema, session_id
            )
        else:
            result = self._stub_generate(natural_query, enriched_schema)

        # ── Store successful generation in memory ─────────
        if result.get("code") and session_id:
            self._add_to_memory(
                session_id,
                natural_query,
                result["code"],
                result.get("explanation", ""),
            )

        return result

    def generate_code_with_correction(
        self,
        natural_query: str,
        schema_summary: str,
        error_message: str,
        previous_code: str,
        column_names: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Self-Correction: ask the LLM to fix its previous failed code.

        ML Concept: Agentic LLM Loop — feed the error back as context.

        Parameters:
            error_message:  The Python exception that was raised
            previous_code:  The code that failed

        Returns: same structure as generate_code()
        """
        correction_query = (
            f"The previous Pandas code failed with error: {error_message!r}\n"
            f"The failing code was: {previous_code}\n"
            f"Original question: {natural_query}\n"
            f"Please write CORRECTED Pandas code that avoids this error."
        )

        if self.use_gemini:
            # ── Use the dedicated correction prompt (not the normal code-gen one)
            from llm.prompt_templates import build_correction_prompt
            correction_prompt = build_correction_prompt(
                natural_query=natural_query,
                schema_summary=schema_summary,
                failed_code=previous_code,
                error_message=error_message,
            )
            try:
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=correction_prompt,
                    config=genai_types.GenerateContentConfig(
                        temperature=0.05,   # Low temp for correction — be precise
                        max_output_tokens=1024,
                        top_p=0.9,
                    ),
                )
                raw = response.text.strip()
                raw = re.sub(r"^```(?:python)?\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
                code = raw.strip()
                if not code or "df" not in code:
                    raise ValueError(f"Gemini returned invalid correction: {repr(code)}")
                return {
                    "code": code,
                    "confidence": 0.90,
                    "explanation": f"[Corrected] Fixed: {error_message[:80]!r}",
                    "engine": f"{settings.GEMINI_MODEL}-correction",
                }
            except Exception as e:
                logger.warning("LLMEngine: Correction failed: %s — falling back to stub", e)
        return self._stub_generate(natural_query, schema_summary)

    def get_memory(self, session_id: str) -> List[ConversationTurn]:
        """Return stored conversation history for a session."""
        return list(self._memory.get(session_id, []))

    def clear_memory(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self._memory:
            del self._memory[session_id]
            logger.info("LLMEngine: Memory cleared for session: %s", session_id)

    # ---------------------------------------------------------
    # Gemini Path (Real AI)
    # ---------------------------------------------------------

    def _gemini_generate(
        self,
        natural_query: str,
        schema_summary: str,
        session_id: Optional[str],
        is_correction: bool = False,
    ) -> Dict[str, Any]:
        """
        Call Google Gemini to generate Pandas code.
        Injects conversation history (ICL) into the prompt.
        Falls back to stub if the API call fails.
        """
        from llm.prompt_templates import build_analysis_prompt

        # ── Build conversation history context ────────────
        history_context = ""
        if session_id and session_id in self._memory:
            turns = list(self._memory[session_id])
            if turns:
                history_lines = [
                    f"[Turn {i+1}] {turn.to_prompt_str()}"
                    for i, turn in enumerate(turns)
                ]
                history_context = (
                    "CONVERSATION HISTORY (use this for context on follow-up questions):\n"
                    + "\n".join(history_lines)
                    + "\n\n"
                )

        prompt = build_analysis_prompt(
            natural_query,
            schema_summary,
            conversation_history=history_context,
        )

        try:
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.05 if is_correction else 0.1,
                    max_output_tokens=1024,
                    top_p=0.9,
                ),
            )

            raw = response.text.strip()

            # Strip markdown code fences if Gemini wraps in ```python ... ```
            raw = re.sub(r"^```(?:python)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            code = raw.strip()

            # Basic sanity check -- must reference df
            if not code or "df" not in code:
                raise ValueError(f"Gemini returned invalid code: {repr(code)}")

            return {
                "code": code,
                "confidence": 0.95 if is_correction else 0.92,
                "explanation": (
                    f"[Corrected] Generated by Gemini AI for: {natural_query!r}"
                    if is_correction
                    else f"Generated by Gemini AI for: {natural_query!r}"
                ),
                "engine": f"{settings.GEMINI_MODEL}-correction" if is_correction else settings.GEMINI_MODEL,
            }

        except Exception as e:
            logger.warning("LLMEngine: Gemini error: %s — falling back to stub", e)
            result = self._stub_generate(natural_query, schema_summary)
            result["explanation"] = f"Gemini unavailable, used fallback. ({e})"
            result["engine"] = "stub-fallback"
            return result

    # ---------------------------------------------------------
    # Memory Management
    # ---------------------------------------------------------

    def _add_to_memory(
        self,
        session_id: str,
        query: str,
        code: str,
        explanation: str,
    ) -> None:
        """Add a Q&A turn to the conversation memory."""
        if session_id not in self._memory:
            self._memory[session_id] = deque(maxlen=self._memory_size)
        self._memory[session_id].append(
            ConversationTurn(query, code, explanation)
        )

    # ---------------------------------------------------------
    # Stub / Fallback Path (Keyword Matching)
    # ---------------------------------------------------------

    def _stub_generate(self, query: str, schema: str) -> Dict[str, Any]:
        """
        Fallback: keyword matching + schema-aware column extraction.
        Active only when GEMINI_API_KEY is not set.
        """
        query_lower = query.lower().strip()

        columns = self._extract_columns_from_schema(schema)
        numeric_cols = columns.get("numeric", [])
        categorical_cols = columns.get("categorical", [])
        datetime_cols = columns.get("datetime", [])

        mentioned_numeric = self._find_mentioned_column(query_lower, numeric_cols)
        mentioned_categorical = self._find_mentioned_column(query_lower, categorical_cols)

        default_num = numeric_cols[0] if numeric_cols else None
        default_cat = categorical_cols[0] if categorical_cols else None

        num = mentioned_numeric or default_num
        cat = mentioned_categorical or default_cat

        code = None
        explanation = None

        if any(kw in query_lower for kw in ["average", "mean", "avg"]):
            if any(kw in query_lower for kw in ["by", "per", "each", "group"]) and cat and num:
                code = f"df.groupby('{cat}')['{num}'].mean().reset_index()"
                explanation = f"Average of '{num}' grouped by '{cat}'"
            elif num:
                code = f"df['{num}'].mean()"
                explanation = f"Overall average of '{num}'"
            else:
                code = "df.describe()"
                explanation = "Descriptive statistics"

        elif any(kw in query_lower for kw in ["sum", "total"]):
            if any(kw in query_lower for kw in ["by", "per", "each", "group"]) and cat and num:
                code = f"df.groupby('{cat}')['{num}'].sum().reset_index()"
                explanation = f"Total '{num}' by '{cat}'"
            elif num:
                code = f"df['{num}'].sum()"
                explanation = f"Sum of '{num}'"
            else:
                code = "df.describe()"
                explanation = "Descriptive statistics"

        elif any(kw in query_lower for kw in ["count", "how many"]):
            if cat:
                code = f"df['{cat}'].value_counts().reset_index()"
                explanation = f"Count of each '{cat}'"
            else:
                code = "df.shape[0]"
                explanation = "Total row count"

        elif any(kw in query_lower for kw in ["max", "maximum", "highest", "top", "largest", "best"]):
            if cat and num:
                code = f"df.groupby('{cat}')['{num}'].max().reset_index().nlargest(10, '{num}')"
                explanation = f"Max '{num}' by '{cat}'"
            elif num:
                code = f"df.nlargest(10, '{num}')"
                explanation = f"Top 10 rows by '{num}'"
            else:
                code = "df.head(10)"
                explanation = "Top 10 rows"

        elif any(kw in query_lower for kw in ["min", "minimum", "lowest", "bottom", "smallest", "worst"]):
            if cat and num:
                code = f"df.groupby('{cat}')['{num}'].min().reset_index().nsmallest(10, '{num}')"
                explanation = f"Min '{num}' by '{cat}'"
            elif num:
                code = f"df.nsmallest(10, '{num}')"
                explanation = f"Bottom 10 rows by '{num}'"
            else:
                code = "df.head(10)"
                explanation = "Bottom rows"

        elif any(kw in query_lower for kw in ["anomal", "outlier", "unusual", "weird"]):
            if num:
                # Z-score based anomaly detection in stub mode
                code = f"df[((df['{num}'] - df['{num}'].mean()) / df['{num}'].std()).abs() > 2]"
                explanation = f"Rows where '{num}' is more than 2 standard deviations from the mean"
            else:
                code = "df.describe()"
                explanation = "Descriptive statistics for anomaly overview"

        elif any(kw in query_lower for kw in ["forecast", "predict", "future", "trend"]):
            if datetime_cols and num:
                dt = datetime_cols[0]
                code = f"df.groupby('{dt}')['{num}'].mean().reset_index()"
                explanation = f"Trend of '{num}' over '{dt}' (use forecast endpoint for predictions)"
            elif num and cat:
                code = f"df.groupby('{cat}')['{num}'].mean().reset_index()"
                explanation = f"'{num}' across '{cat}'"
            else:
                code = "df.head(20)"
                explanation = "Dataset preview"

        elif any(kw in query_lower for kw in ["cluster", "group", "segment"]):
            if num:
                code = f"df.groupby('{cat}')['{num}'].agg(['mean', 'count']).reset_index()" if cat else f"df['{num}'].describe()"
                explanation = f"Grouped statistics for clustering context (use cluster endpoint for K-Means)"
            else:
                code = "df.describe()"
                explanation = "Descriptive statistics"

        elif any(kw in query_lower for kw in ["describe", "summary", "statistics", "stats", "overview"]):
            code = "df.describe()"
            explanation = "Descriptive statistics for all numeric columns"

        elif any(kw in query_lower for kw in ["distribution", "spread", "breakdown"]):
            if cat:
                code = f"df['{cat}'].value_counts().reset_index()"
                explanation = f"Distribution of '{cat}'"
            elif num:
                code = f"df['{num}'].describe()"
                explanation = f"Distribution of '{num}'"
            else:
                code = "df.describe()"
                explanation = "Distribution of all columns"

        elif any(kw in query_lower for kw in ["correlation", "correlate", "relationship"]):
            code = "df.corr(numeric_only=True)"
            explanation = "Correlation matrix"

        elif any(kw in query_lower for kw in ["trend", "over time", "timeline", "time series"]):
            if datetime_cols and num:
                dt = datetime_cols[0]
                code = f"df.groupby('{dt}')['{num}'].mean().reset_index()"
                explanation = f"Trend of '{num}' over '{dt}'"
            elif num and cat:
                code = f"df.groupby('{cat}')['{num}'].mean().reset_index()"
                explanation = f"'{num}' across '{cat}'"
            else:
                code = "df.head(20)"
                explanation = "Dataset preview"

        elif any(kw in query_lower for kw in ["compare", "comparison", "versus", "vs"]):
            if cat and num:
                code = f"df.groupby('{cat}')['{num}'].mean().reset_index()"
                explanation = f"Comparison of '{num}' across '{cat}'"
            else:
                code = "df.describe()"
                explanation = "Comparison statistics"

        elif any(kw in query_lower for kw in ["unique", "distinct"]):
            if cat:
                code = f"df['{cat}'].unique().tolist()"
                explanation = f"Unique values in '{cat}'"
            else:
                code = "df.nunique()"
                explanation = "Unique count per column"

        elif any(kw in query_lower for kw in ["missing", "null", "empty", "na"]):
            code = "df.isnull().sum().reset_index().rename(columns={'index': 'column', 0: 'missing_count'})"
            explanation = "Missing value count per column"

        elif any(kw in query_lower for kw in ["show", "display", "list", "view", "see", "give"]):
            if any(kw in query_lower for kw in ["all", "everything", "full"]):
                code = "df.head(50)"
                explanation = "First 50 rows"
            elif cat and num:
                code = f"df.groupby('{cat}')['{num}'].mean().reset_index()"
                explanation = f"'{num}' by '{cat}'"
            else:
                code = "df.head(20)"
                explanation = "First 20 rows"

        else:
            if mentioned_numeric and mentioned_categorical:
                code = f"df.groupby('{mentioned_categorical}')['{mentioned_numeric}'].mean().reset_index()"
                explanation = f"Average '{mentioned_numeric}' by '{mentioned_categorical}'"
            elif mentioned_categorical:
                code = f"df['{mentioned_categorical}'].value_counts().reset_index()"
                explanation = f"Distribution of '{mentioned_categorical}'"
            elif mentioned_numeric:
                code = f"df['{mentioned_numeric}'].describe()"
                explanation = f"Statistics for '{mentioned_numeric}'"
            else:
                code = "df.head(10)"
                explanation = "Dataset preview"

        return {
            "code": code,
            "confidence": 0.75,
            "explanation": explanation,
            "engine": "keyword-stub",
        }

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _find_mentioned_column(self, query: str, column_list: List[str]) -> str:
        if not column_list:
            return None
        sorted_cols = sorted(column_list, key=len, reverse=True)
        for col in sorted_cols:
            col_lower = col.lower()
            col_space = col_lower.replace("_", " ")
            if col_lower in query or col_space in query:
                return col
        return None

    def _extract_columns_from_schema(self, schema: str) -> Dict[str, list]:
        columns = {"numeric": [], "categorical": [], "datetime": [], "boolean": []}
        for line in schema.split("\n"):
            line = line.strip()
            if not line.startswith("- "):
                continue
            content = line[2:]
            paren_idx = content.find("(")
            if paren_idx == -1:
                continue
            col_name = content[:paren_idx].strip()
            rest = content[paren_idx + 1:]
            close_paren = rest.find(")")
            if close_paren == -1:
                continue
            col_type = rest[:close_paren].strip().lower()
            if col_type in columns:
                columns[col_type].append(col_name)
        return columns


# -- Module-level singleton --
llm_engine = LLMEngine()
