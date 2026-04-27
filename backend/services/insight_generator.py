"""
============================================================
Insight Generator — Analyst-style textual insights
============================================================
Generates contextual, readable insights: not raw stats,
but observations with comparisons, rankings, and meaning.
E.g.:  "Kolkata records the highest NO₂ at 56.25 — nearly
        8× higher than Aizawl, the cleanest city (7.29)."
============================================================
"""

import pandas as pd
from typing import Dict, Any, List


def _fmt(val: float) -> str:
    """Format a float cleanly — 2 dp, comma-separated thousands."""
    if abs(val) >= 1000:
        return f"{val:,.1f}"
    if val == int(val):
        return str(int(val))
    return f"{val:.2f}"


def _times_diff(a: float, b: float) -> str:
    """Return a readable ratio string like '3.2× higher'."""
    if b == 0:
        return ""
    ratio = a / b
    if ratio >= 1.5:
        return f"{ratio:.1f}× higher"
    return ""


def generate_insights(data: List[Dict], columns: List[str]) -> Dict[str, Any]:
    """
    Analyse the query result and produce analyst-style insights.

    Returns:
        {
            "summary":    str,
            "highlights": list of str,
            "row_count":  int
        }
    """
    if not data or not columns:
        return {
            "summary":    "No data available to generate insights.",
            "highlights": [],
            "row_count":  0,
        }

    df         = pd.DataFrame(data)
    highlights = []
    row_count  = len(df)

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols     = df.select_dtypes(include=["object"]).columns.tolist()

    # Detect the label/grouping column (e.g. city, year, month)
    label_col = cat_cols[0] if cat_cols else None

    # Skip columns that look like years or row indices (not real metrics)
    def _is_year_col(col: str, series: pd.Series) -> bool:
        if series.empty:
            return False
        vals = series.dropna()
        return col.lower() in ("year", "index") or bool(
            vals.between(1900, 2100).all() and vals.nunique() <= 20
        )

    # Promote year column to label if it's numeric
    if not label_col:
        for col in numeric_cols[:]:
            s = df[col].dropna()
            if _is_year_col(col, s):
                label_col    = col
                numeric_cols = [c for c in numeric_cols if c != col]
                break

    # ── Per-numeric-column insights ──────────────────────────
    for col in numeric_cols[:2]:   # cap at 2 metrics to stay focused
        series   = df[col].dropna()
        col_disp = (
            col.replace("_", ".").upper()
            if col.lower().startswith("pm")
            else col.replace("_", " ").upper()
        )

        if series.empty:
            continue

        max_val  = series.max()
        min_val  = series.min()
        mean_val = series.mean()
        spread   = max_val - min_val

        # ── When we have a label column (e.g. city, year) ──
        if label_col and label_col in df.columns:
            max_label = df.loc[series.idxmax(), label_col]
            min_label = df.loc[series.idxmin(), label_col]
            label_disp  = label_col.replace("_", " ").title()
            # Correct pluralization: City→Cities, Year→Years, etc.
            if label_disp.endswith("y"):
                label_plural = label_disp[:-1] + "ies"
            else:
                label_plural = label_disp + "s"
            ratio_str   = _times_diff(max_val, min_val)

            # Top & bottom with comparison
            if ratio_str:
                highlights.append(
                    f"📈 Highest {col_disp}: **{max_label}** at {_fmt(max_val)}"
                    f" — {ratio_str} than {min_label} ({_fmt(min_val)})"
                )
            else:
                highlights.append(
                    f"📈 Highest {col_disp}: **{max_label}** ({_fmt(max_val)})"
                )
                highlights.append(
                    f"📉 Lowest {col_disp}: **{min_label}** ({_fmt(min_val)})"
                )

            # Overall average with context
            above_avg = int((series > mean_val).sum())
            highlights.append(
                f"📊 Overall average: {_fmt(mean_val)}"
                f" — {above_avg} out of {row_count} {label_plural} are above this"
            )

            # Top 3 if enough rows
            if row_count >= 5:
                top3  = df.nlargest(3, col)
                names = ", ".join(
                    f"{row[label_col]} ({_fmt(row[col])})"
                    for _, row in top3.iterrows()
                )
                highlights.append(f"🏆 Top 3 by {col_disp}: {names}")

            # Spread observation
            if spread > 0:
                spread_pct = (spread / mean_val) * 100
                if spread_pct > 100:
                    highlights.append(
                        f"⚡ Large variation detected — values range from {_fmt(min_val)} "
                        f"to {_fmt(max_val)} ({_fmt(spread_pct)}% spread), "
                        f"indicating significant differences across {label_plural}"
                    )

        # ── Purely numeric / time-series result ────────────
        else:
            highlights.append(
                f"📈 Peak value: {_fmt(max_val)}   📉 Lowest: {_fmt(min_val)}   📊 Average: {_fmt(mean_val)}"
            )

            # Trend (first-half vs second-half)
            if row_count >= 4:
                first_half  = series.head(row_count // 2).mean()
                second_half = series.tail(row_count // 2).mean()
                if first_half > 0:
                    change_pct = (second_half - first_half) / first_half * 100
                    if change_pct > 10:
                        highlights.append(
                            f"⬆️ Upward trend: values increased by ~{_fmt(change_pct)}% "
                            f"compared to the earlier period"
                        )
                    elif change_pct < -10:
                        highlights.append(
                            f"⬇️ Downward trend: values decreased by ~{_fmt(abs(change_pct))}% "
                            f"compared to the earlier period"
                        )
                    else:
                        highlights.append(
                            f"➡️ Relatively stable — values changed by only {_fmt(abs(change_pct))}% "
                            f"over the period"
                        )

    # ── Single-value result (scalar aggregation) ──────────────
    if row_count == 1 and len(numeric_cols) == 1:
        val = df[numeric_cols[0]].iloc[0]
        col_disp = numeric_cols[0].replace("_", " ").upper()
        highlights = [f"📊 The computed {col_disp} is **{_fmt(val)}**"]

    # ── Correlation result (2×2 matrix) ─────────────────────
    if row_count == 2 and len(numeric_cols) == 2 and len(cat_cols) == 0:
        # It's a 2×2 correlation matrix
        corr_val = df[numeric_cols[1]].iloc[1]   # off-diagonal
        def _disp(c):
            return c.replace("_", ".").upper() if c.lower().startswith("pm") else c.replace("_", " ").upper()
        col_a = _disp(numeric_cols[0])
        col_b = _disp(numeric_cols[1])
        strength = (
            "very strong positive" if corr_val >= 0.9 else
            "strong positive"      if corr_val >= 0.7 else
            "moderate positive"    if corr_val >= 0.4 else
            "weak positive"        if corr_val >= 0.1 else
            "very strong negative" if corr_val <= -0.9 else
            "strong negative"      if corr_val <= -0.7 else
            "weak negative"
        )
        highlights = [
            f"🔗 Correlation between {col_a} and {col_b}: **{_fmt(corr_val)}** ({strength} correlation)",
            f"📌 This means that when {col_a} increases, {col_b} tends to "
            + ("increase proportionally as well." if corr_val > 0 else "decrease."),
        ]

    # ── Plain-English summary line ────────────────────────────
    if row_count == 1:
        summary = "The query returned a single computed value."
    elif label_col and numeric_cols:
        label_disp = label_col.replace("_", " ").title()
        metric     = numeric_cols[0].replace("_", " ").upper()
        summary = (
            f"Comparing {metric} across {row_count} {label_disp}s. "
            f"Use the chart to spot which {label_disp}s stand out."
        )
    elif numeric_cols and not cat_cols:
        summary = (
            f"Showing {row_count} data points for "
            f"{', '.join(c.replace('_', ' ').upper() for c in numeric_cols[:2])}. "
            f"Look for trends and peaks in the chart above."
        )
    else:
        summary = f"The result contains {row_count} rows across {len(columns)} columns."

    return {
        "summary":    summary,
        "highlights": highlights[:6],   # max 6 bullets
        "row_count":  row_count,
    }
