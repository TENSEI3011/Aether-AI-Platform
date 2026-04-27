"""
============================================================
Visualization Selector — Automatically chooses chart type
============================================================
Analyses the query result shape and column types to select
the most appropriate visualization:
  - Category vs Numeric → Bar chart
  - Datetime vs Numeric → Line chart
  - Single distribution  → Pie chart
  - Large table           → Data table
  - Two numeric cols      → Scatter chart
  - Single numeric col    → Histogram
  - Square numeric matrix → Heatmap (e.g. correlation)

Supports manual override via `graph_type` parameter.
============================================================
"""

import pandas as pd
from typing import Dict, Any, List, Optional


def select_visualization(
    data: List[Dict],
    columns: List[str],
    row_count: int,
    graph_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyse query result and recommend a chart type.
    If `graph_type` is provided and is not 'auto', use that override.

    Returns:
        {
            "chart_type": "bar"|"line"|"pie"|"table"|"scatter"|"histogram"|"heatmap",
            "x_axis": str or None,
            "y_axis": str or None,
            "reason": str
        }
    """
    if not data or not columns:
        return {
            "chart_type": "table",
            "x_axis": None,
            "y_axis": None,
            "reason": "No data to visualize",
        }

    # Convert to DataFrame for analysis
    df = pd.DataFrame(data)

    # ── Identify column types ─────────────────────────────
    numeric_cols = []
    categorical_cols = []
    datetime_cols = []

    for col in columns:
        if col not in df.columns:
            continue
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            numeric_cols.append(col)
        else:
            # Try datetime
            try:
                pd.to_datetime(series)
                datetime_cols.append(col)
            except (ValueError, TypeError):
                categorical_cols.append(col)

    # ── Determine axis candidates ─────────────────────────
    x_axis = None
    y_axis = None

    if datetime_cols:
        x_axis = datetime_cols[0]
    elif categorical_cols:
        x_axis = categorical_cols[0]
    elif len(numeric_cols) >= 2:
        x_axis = numeric_cols[0]

    if numeric_cols:
        # Pick the first numeric col that isn't already x_axis
        for nc in numeric_cols:
            if nc != x_axis:
                y_axis = nc
                break
        if y_axis is None:
            y_axis = numeric_cols[0]

    # ── Manual override ───────────────────────────────────
    if graph_type and graph_type != "auto":
        valid_types = {"bar", "line", "pie", "table", "scatter", "histogram", "heatmap"}
        if graph_type in valid_types:
            return {
                "chart_type": graph_type,
                "x_axis": x_axis,
                "y_axis": y_axis,
                "reason": f"User selected '{graph_type}' chart",
            }

    # ── Auto-select decision logic ────────────────────────

    # Case 1: Heatmap — square all-numeric result (e.g. df.corr())
    if (len(numeric_cols) >= 3 and not categorical_cols and not datetime_cols
            and abs(row_count - len(numeric_cols)) <= 2):
        return {
            "chart_type": "heatmap",
            "x_axis": columns[0],
            "y_axis": None,
            "reason": f"Square numeric matrix ({row_count}×{len(numeric_cols)}) — correlation heatmap",
        }

    # Case 2: Datetime + Numeric → Line chart
    if datetime_cols and numeric_cols:
        return {
            "chart_type": "line",
            "x_axis": datetime_cols[0],
            "y_axis": y_axis,
            "reason": f"Datetime '{datetime_cols[0]}' vs numeric '{y_axis}'",
        }

    # Case 3: Two+ numeric, no categories, many rows → Scatter
    if len(numeric_cols) >= 2 and not categorical_cols and row_count > 10:
        return {
            "chart_type": "scatter",
            "x_axis": numeric_cols[0],
            "y_axis": numeric_cols[1],
            "reason": f"Two numeric columns with {row_count} rows — scatter plot",
        }

    # Case 4: Categorical + Numeric → Bar or Pie chart
    if categorical_cols and numeric_cols:
        unique_count = df[categorical_cols[0]].nunique()
        if unique_count <= 6 and len(numeric_cols) == 1:
            return {
                "chart_type": "pie",
                "x_axis": categorical_cols[0],
                "y_axis": y_axis,
                "reason": f"Small category set ({unique_count} values) — pie chart",
            }
        return {
            "chart_type": "bar",
            "x_axis": categorical_cols[0],
            "y_axis": y_axis,
            "reason": f"Categorical '{categorical_cols[0]}' vs numeric '{y_axis}'",
        }

    # Case 5: Single numeric column with enough rows → Histogram
    if len(numeric_cols) == 1 and not categorical_cols and row_count > 5:
        return {
            "chart_type": "histogram",
            "x_axis": numeric_cols[0],
            "y_axis": None,
            "reason": f"Single numeric '{numeric_cols[0]}' distribution — histogram",
        }

    # Case 6: Two numeric, few rows → Bar
    if len(numeric_cols) >= 2:
        return {
            "chart_type": "bar",
            "x_axis": numeric_cols[0],
            "y_axis": numeric_cols[1],
            "reason": "Two numeric columns — bar chart",
        }

    # Case 7: Single column (distribution)
    if len(columns) == 1 or (len(columns) == 2 and "index" in columns):
        value_col = [c for c in columns if c != "index"]
        idx_col = "index" if "index" in columns else columns[0]
        if value_col:
            return {
                "chart_type": "pie" if row_count <= 10 else "bar",
                "x_axis": idx_col,
                "y_axis": value_col[0],
                "reason": "Single value distribution",
            }

    # Default: Data table
    return {
        "chart_type": "table",
        "x_axis": None,
        "y_axis": None,
        "reason": f"Complex result ({row_count} rows, {len(columns)} cols) — table view",
    }
