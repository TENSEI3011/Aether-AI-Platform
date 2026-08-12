"""
============================================================
Insight Generator — AI-powered textual insights
============================================================
PRIMARY:  Google Gemini generates natural language insights
FALLBACK: Statistical analysis (max/min/trend highlights)

Upgraded to use Gemini when GEMINI_API_KEY is available.
============================================================
"""

import logging
import pandas as pd
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from google.genai import types as genai_types
    _GENAI_TYPES_AVAILABLE = True
except ImportError:
    _GENAI_TYPES_AVAILABLE = False

from core.config import settings


def generate_insights(
    data: List[Dict],
    columns: List[str],
    natural_query: str = "",
) -> Dict[str, Any]:
    """
    Analyse the query result and produce textual insights.

    Uses Gemini AI when GEMINI_API_KEY is set.
    Falls back to statistical analysis otherwise.

    Returns:
        {
            "summary": str,
            "highlights": list of str,
            "row_count": int,
            "engine": str   ("gemini" or "statistical")
        }
    """
    if not data or not columns:
        return {
            "summary": "No data available to generate insights.",
            "highlights": [],
            "row_count": 0,
            "engine": "none",
        }

    # ── Reuse the singleton LLMEngine client (avoids creating a new client per request) ──
    from llm.llm_engine import llm_engine
    use_gemini = llm_engine.use_gemini

    # ── Also build the statistical highlights (always computed) ──
    statistical = _statistical_insights(data, columns)

    if use_gemini:
        try:
            prompt = _build_insight_prompt(natural_query, data, columns)
            response = llm_engine.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.3,       # Slightly lower for more factual insights
                    max_output_tokens=512, # Doubled: 256 was cutting insights mid-sentence
                ),
            )
            ai_summary = response.text.strip()

            return {
                "summary": ai_summary,
                "highlights": statistical["highlights"],  # keep stats too
                "row_count": len(data),
                "engine": "gemini",
            }
        except Exception as e:
            logger.warning("InsightGenerator: Gemini error: %s — using statistical fallback", e)

    # ── Statistical fallback ──────────────────────────────
    return {**statistical, "engine": "statistical"}


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def _build_insight_prompt(natural_query: str, data: List[Dict], columns: List[str]) -> str:
    """Build a concise Gemini prompt using column statistics (not raw rows).

    Using aggregated stats instead of raw rows gives Gemini richer signal
    in fewer tokens: the model can cite real numbers without wading through
    potentially noisy individual records.
    """
    df = pd.DataFrame(data)
    stats_lines = []

    for col in columns:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            continue
        if pd.api.types.is_numeric_dtype(series):
            stats_lines.append(
                f"  {col} (numeric): min={series.min():.2f}, max={series.max():.2f}, "
                f"mean={series.mean():.2f}, std={series.std():.2f}"
            )
        else:
            top = series.value_counts().head(3)
            top_str = ", ".join(f"'{v}' ({c}x)" for v, c in top.items())
            stats_lines.append(f"  {col} (categorical): top values — {top_str}")

    stats_block = "\n".join(stats_lines) if stats_lines else "(no stats available)"

    return f"""You are a concise data analyst. A user asked: "{natural_query or 'Analyse this data'}"

The query result has {len(data)} rows and {len(columns)} columns.
Column statistics (use these exact numbers in your response):
{stats_block}

Write EXACTLY 3 bullet points (each starting with •). Each bullet must:
  1. Cite at least one specific number from the statistics above
  2. Be under 35 words
  3. Be directly relevant to the user's question

Format:
• [Key finding with a specific number]
• [Trend or comparison with a specific number]
• [Actionable insight or recommendation]

Do not include any other text before or after the 3 bullets."""


def _statistical_insights(data: List[Dict], columns: List[str]) -> Dict[str, Any]:
    """Original statistical insight logic — always used for highlights."""
    df = pd.DataFrame(data)
    highlights = []
    row_count = len(df)

    summary_parts = [f"The result contains {row_count} row(s) and {len(columns)} column(s)."]

    # ── Numeric column insights ───────────────────────────
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue

        max_val = series.max()
        min_val = series.min()
        mean_val = round(series.mean(), 2)
        highlights.append(f"'{col}': max = {max_val}, min = {min_val}, average = {mean_val}")

        # Simple trend detection
        if len(series) >= 3:
            first_third = series.head(len(series) // 3).mean()
            last_third = series.tail(len(series) // 3).mean()
            if last_third > first_third * 1.1:
                highlights.append(f"'{col}' shows an upward trend")
            elif last_third < first_third * 0.9:
                highlights.append(f"'{col}' shows a downward trend")

    # ── Categorical column insights ───────────────────────
    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
    for col in cat_cols[:2]:
        value_counts = df[col].value_counts()
        if not value_counts.empty:
            top_value = value_counts.index[0]
            top_count = int(value_counts.iloc[0])
            highlights.append(f"Most frequent '{col}': '{top_value}' ({top_count} occurrences)")

    if numeric_cols:
        summary_parts.append(f"Numeric columns analysed: {', '.join(numeric_cols)}.")
    if highlights:
        summary_parts.append("Key highlights are listed below.")

    return {
        "summary": " ".join(summary_parts),
        "highlights": highlights,
        "row_count": row_count,
    }
