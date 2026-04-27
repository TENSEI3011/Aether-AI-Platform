"""
============================================================
Data Profiler — Rich dataset profiling service
============================================================
Generates comprehensive dataset statistics including:
  - Shape & memory usage
  - Missing value analysis (count + percentage)
  - Data type distribution
  - Top values for categorical columns
  - Descriptive statistics for numeric columns
  - Correlation matrix for numeric columns
============================================================
"""

import pandas as pd
from typing import Dict, Any, List


def generate_full_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a comprehensive data profile for the given DataFrame.

    Returns a dict with sections:
      - overview: rows, columns, memory, duplicates
      - missing_values: per-column count and percentage
      - data_types: type distribution summary
      - categorical_summary: top 5 values per categorical column
      - numeric_summary: descriptive stats per numeric column
      - correlation_matrix: pairwise correlations for numeric columns
    """
    rows, cols = df.shape

    # ── Overview ──────────────────────────────────────────
    overview = {
        "rows": int(rows),
        "columns": int(cols),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
        "duplicate_rows": int(df.duplicated().sum()),
        "column_names": list(df.columns),
    }

    # ── Missing Values ────────────────────────────────────
    missing_counts = df.isnull().sum()
    missing_values = []
    for col in df.columns:
        count = int(missing_counts[col])
        missing_values.append({
            "column": col,
            "missing_count": count,
            "missing_percent": round((count / rows) * 100, 1) if rows > 0 else 0,
        })

    # ── Data Type Distribution ────────────────────────────
    type_counts = {}
    column_types = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        # Map to semantic types
        if pd.api.types.is_numeric_dtype(df[col]):
            semantic = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            semantic = "datetime"
        elif pd.api.types.is_bool_dtype(df[col]):
            semantic = "boolean"
        else:
            semantic = "categorical"

        type_counts[semantic] = type_counts.get(semantic, 0) + 1
        column_types.append({
            "column": col,
            "dtype": dtype,
            "semantic_type": semantic,
        })

    data_types = {
        "distribution": type_counts,
        "columns": column_types,
    }

    # ── Categorical Summary (top 5 values) ────────────────
    categorical_summary = []
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    for col in cat_cols[:10]:  # Limit to 10 columns
        vc = df[col].value_counts().head(5)
        top_values = [
            {"value": str(val), "count": int(cnt)}
            for val, cnt in vc.items()
        ]
        categorical_summary.append({
            "column": col,
            "unique_count": int(df[col].nunique()),
            "top_values": top_values,
        })

    # ── Numeric Summary ───────────────────────────────────
    numeric_summary = []
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if num_cols:
        desc = df[num_cols].describe()
        for col in num_cols:
            stats = desc[col].to_dict()
            numeric_summary.append({
                "column": col,
                "count": int(stats.get("count", 0)),
                "mean": round(stats.get("mean", 0), 2),
                "std": round(stats.get("std", 0), 2),
                "min": round(stats.get("min", 0), 2),
                "q25": round(stats.get("25%", 0), 2),
                "median": round(stats.get("50%", 0), 2),
                "q75": round(stats.get("75%", 0), 2),
                "max": round(stats.get("max", 0), 2),
            })

    # ── Correlation Matrix ────────────────────────────────
    correlation_matrix = []
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        for i, col1 in enumerate(num_cols):
            for col2 in num_cols[i:]:
                val = corr.loc[col1, col2]
                if pd.notna(val):
                    correlation_matrix.append({
                        "col1": col1,
                        "col2": col2,
                        "value": round(float(val), 3),
                    })

    return {
        "overview": overview,
        "missing_values": missing_values,
        "data_types": data_types,
        "categorical_summary": categorical_summary,
        "numeric_summary": numeric_summary,
        "correlation_matrix": correlation_matrix,
    }
