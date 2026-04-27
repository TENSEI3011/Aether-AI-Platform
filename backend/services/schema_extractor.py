"""
============================================================
Schema Extractor — Extracts column metadata from DataFrames
============================================================
Detects data types (numeric, categorical, datetime),
generates column metadata, and produces a schema summary
string suitable for LLM context injection.
============================================================
"""

import pandas as pd
from typing import Dict, Any, List


def classify_column_type(series: pd.Series) -> str:
    """
    Classify a single column as 'numeric', 'categorical',
    'datetime', or 'boolean'.
    """
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    # Try to parse as datetime
    try:
        pd.to_datetime(series.dropna().head(20))
        return "datetime"
    except (ValueError, TypeError):
        pass
    return "categorical"


def extract_column_metadata(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract metadata for every column: name, dtype,
    semantic type, unique count, sample values, and nulls.
    """
    metadata = []
    for col in df.columns:
        series = df[col]
        col_type = classify_column_type(series)
        info = {
            "name": col,
            "dtype": str(series.dtype),
            "semantic_type": col_type,
            "null_count": int(series.isnull().sum()),
            "unique_count": int(series.nunique()),
            "sample_values": series.dropna().head(5).tolist(),
        }
        metadata.append(info)
    return metadata


def extract_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Full schema extraction: column metadata + summary stats.
    """
    columns = extract_column_metadata(df)
    return {
        "total_rows": int(df.shape[0]),
        "total_columns": int(df.shape[1]),
        "columns": columns,
    }


def generate_schema_summary(schema: Dict[str, Any]) -> str:
    """
    Produce a human-readable schema summary string that
    can be injected into the LLM prompt as context.

    Example output:
        Dataset has 1000 rows and 5 columns.
        Columns:
        - age (numeric): 0 nulls, 45 unique values
        - city (categorical): 2 nulls, 12 unique values
        ...
    """
    lines = [
        f"Dataset has {schema['total_rows']} rows and {schema['total_columns']} columns.",
        "Columns:"
    ]
    for col in schema["columns"]:
        lines.append(
            f"  - {col['name']} ({col['semantic_type']}): "
            f"{col['null_count']} nulls, {col['unique_count']} unique values. "
            f"Sample: {col['sample_values'][:3]}"
        )
    return "\n".join(lines)
