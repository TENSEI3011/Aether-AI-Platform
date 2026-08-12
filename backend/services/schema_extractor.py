"""
============================================================
Schema Extractor — Extracts column metadata from DataFrames
============================================================
Detects data types (numeric, categorical, datetime),
generates column metadata, and produces a schema summary
string suitable for LLM context injection.

ENHANCED:
  ✅ Datetime classifier now requires ≥80% parse rate to
     avoid false positives on string columns like "Category".
  ✅ Schema summary now includes min/max/mean for numeric
     columns and top categories for categoricals — gives
     the LLM concrete range context for filter thresholds.
  ✅ ID column detection: numeric cols where unique_count ==
     total_rows are flagged as "id" — LLM won't aggregate them.
  ✅ Binary flag detection: numeric cols with only 2 distinct
     values (0/1) are reclassified as "boolean" so they don't
     skew numeric summaries or get averaged.
============================================================
"""

import pandas as pd
from typing import Dict, Any, List


def _is_id_column(series: pd.Series, total_rows: int) -> bool:
    """
    True if this numeric column looks like a row identifier.
    Heuristic: unique_count == total_rows (every value is unique).
    """
    if not pd.api.types.is_numeric_dtype(series):
        return False
    unique = series.nunique()
    non_null = series.count()
    return non_null > 0 and unique == non_null and unique >= total_rows * 0.98


def _is_binary_flag(series: pd.Series) -> bool:
    """
    True if this numeric column contains only 0 and 1 values.
    These are boolean flags, not meaningful quantities to aggregate.
    """
    if not pd.api.types.is_numeric_dtype(series):
        return False
    unique_vals = set(series.dropna().unique())
    return unique_vals <= {0, 1, 0.0, 1.0}


def classify_column_type(series: pd.Series, total_rows: int = 0) -> str:
    """
    Classify a single column as 'numeric', 'categorical',
    'datetime', 'boolean', or 'id'.

    FIX: datetime detection now requires ≥80% of sample values
    to successfully parse as dates. This prevents columns like
    "Category", "Name", or "Status" from being misclassified.

    NEW: ID columns and binary flags are detected and classified
    separately so the LLM doesn't try to aggregate them.
    """
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        # Check for binary flag first (0/1 only)
        if _is_binary_flag(series):
            return "boolean"
        # Check for ID-like column
        if total_rows > 0 and _is_id_column(series, total_rows):
            return "id"
        return "numeric"

    # Threshold-based datetime detection (prevents false positives)
    try:
        sample = series.dropna().head(30)
        if len(sample) == 0:
            return "categorical"
        parsed = pd.to_datetime(sample, errors="coerce")
        parse_rate = parsed.notna().sum() / len(sample)
        if parse_rate >= 0.80:
            return "datetime"
    except (ValueError, TypeError):
        pass

    return "categorical"


def extract_column_metadata(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract metadata for every column: name, dtype,
    semantic type, unique count, sample values, nulls,
    and numeric stats (min, max, mean) for numeric columns.
    """
    total_rows = len(df)
    metadata = []
    for col in df.columns:
        series = df[col]
        col_type = classify_column_type(series, total_rows)

        info = {
            "name":          col,
            "dtype":         str(series.dtype),
            "semantic_type": col_type,
            "null_count":    int(series.isnull().sum()),
            "unique_count":  int(series.nunique()),
            "sample_values": series.dropna().head(5).tolist(),
        }

        # ── Numeric stats: give LLM concrete range context ──
        if col_type == "numeric":
            clean = series.dropna()
            if not clean.empty:
                info["min"]  = round(float(clean.min()), 4)
                info["max"]  = round(float(clean.max()), 4)
                info["mean"] = round(float(clean.mean()), 4)

        # ── Top categories: help LLM know valid filter values ──
        if col_type == "categorical":
            top = series.value_counts().head(5).index.tolist()
            info["top_values"] = [str(v) for v in top]

        metadata.append(info)
    return metadata


def extract_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Full schema extraction: column metadata + summary stats.
    """
    columns = extract_column_metadata(df)
    return {
        "total_rows":    int(df.shape[0]),
        "total_columns": int(df.shape[1]),
        "columns":       columns,
    }


def generate_schema_summary(schema: Dict[str, Any]) -> str:
    """
    Produce a human-readable schema summary string that
    can be injected into the LLM prompt as context.

    ENHANCED: Numeric columns include min/max/mean. Categorical
    columns include their top values. ID columns and boolean flags
    are annotated so the LLM doesn't aggregate them incorrectly.

    Example output:
        Dataset has 1000 rows and 5 columns.
        Columns:
        - age (numeric): range 18-80, mean 34.5, 0 nulls
        - city (categorical): top values: ['NYC', 'LA'], 12 unique
        - user_id (id): do NOT aggregate — unique identifier
        - is_active (boolean): binary flag (0/1)
        ...
    """
    lines = [
        f"Dataset has {schema['total_rows']} rows and {schema['total_columns']} columns.",
        "Columns:"
    ]
    for col in schema["columns"]:
        col_type = col["semantic_type"]

        if col_type == "id":
            detail = "unique row identifier — do NOT aggregate or average this column"
        elif col_type == "boolean":
            detail = (
                f"binary flag (0/1 or True/False), "
                f"{col['null_count']} nulls. Use for filtering, not averaging."
            )
        elif col_type == "numeric" and "min" in col:
            detail = (
                f"range {col['min']}-{col['max']}, mean {col['mean']}, "
                f"{col['null_count']} nulls, {col['unique_count']} unique. "
                f"Sample: {col['sample_values'][:3]}"
            )
        elif col_type == "categorical" and "top_values" in col:
            detail = (
                f"top values: {col['top_values']}, "
                f"{col['null_count']} nulls, {col['unique_count']} unique"
            )
        else:
            detail = (
                f"{col['null_count']} nulls, {col['unique_count']} unique. "
                f"Sample: {col['sample_values'][:3]}"
            )

        lines.append(f"  - {col['name']} ({col_type}): {detail}")

    return "\n".join(lines)
