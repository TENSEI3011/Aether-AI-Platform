"""
============================================================
Insight Generator — AI-powered textual insights
============================================================
PRIMARY:  Google Gemini generates natural language insights
FALLBACK: Statistical analysis (max/min/trend highlights)

Upgraded to use Gemini when GEMINI_API_KEY is available.
============================================================
"""

import os
import pandas as pd
from typing import Dict, Any, List

# ── Use the new google.genai SDK ────────────────────────────────
try:
    from google import genai
    from google.genai import types as genai_types
    _GEMINI_SDK_AVAILABLE = True
except ImportError:
    _GEMINI_SDK_AVAILABLE = False


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

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    use_gemini = _GEMINI_SDK_AVAILABLE and bool(api_key)

    # ── Also build the statistical highlights (always computed) ──
    statistical = _statistical_insights(data, columns)

    if use_gemini:
        try:
            client = genai.Client(api_key=api_key)

            prompt = _build_insight_prompt(natural_query, data, columns)
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=256,
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
            print(f"[InsightGenerator] Gemini error: {e} — using statistical fallback")

    # ── Statistical fallback ──────────────────────────────
    return {**statistical, "engine": "statistical"}


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def _build_insight_prompt(natural_query: str, data: List[Dict], columns: List[str]) -> str:
    """Build a concise Gemini prompt for business insights."""
    sample = data[:8]  # first 8 rows for context
    return f"""You are a data analyst. A user asked: "{natural_query or 'Analyse this data'}"

The result has {len(data)} rows and these columns: {columns}
Sample data (first {len(sample)} rows): {sample}

Write 2-3 short, specific business insights in plain English.
Use actual numbers from the data. Be direct — no fluff, no bullet symbols."""


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
