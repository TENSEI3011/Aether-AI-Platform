"""
============================================================
Data Validator — Validates uploaded datasets
============================================================
Checks file format, detects missing values, duplicates,
invalid types, and generates a data profile summary.
============================================================
"""

import pandas as pd
from typing import Dict, Any


def validate_file_format(filename: str) -> bool:
    """Check that uploaded file is CSV or Excel."""
    allowed = (".csv", ".xlsx", ".xls")
    return any(filename.lower().endswith(ext) for ext in allowed)


def load_dataframe(filepath: str) -> pd.DataFrame:
    """
    Load a CSV or Excel file into a Pandas DataFrame.
    Raises ValueError if the file format is unsupported.
    """
    if filepath.endswith(".csv"):
        return pd.read_csv(filepath)
    elif filepath.endswith((".xlsx", ".xls")):
        return pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}")


def detect_missing_values(df: pd.DataFrame) -> Dict[str, int]:
    """Return a dict of column → count of missing values."""
    return df.isnull().sum().to_dict()


def detect_duplicates(df: pd.DataFrame) -> int:
    """Return the number of duplicate rows."""
    return int(df.duplicated().sum())


def detect_invalid_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    Return a dict of column → detected dtype.
    Flags columns that have mixed types by checking if
    conversion to numeric fails on seemingly numeric columns.
    """
    type_report = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        if dtype == "object":
            # Try to see if it can be numeric
            numeric_check = pd.to_numeric(df[col], errors="coerce")
            non_null_original = df[col].dropna().shape[0]
            non_null_numeric = numeric_check.dropna().shape[0]
            if non_null_original > 0 and non_null_numeric / non_null_original > 0.8:
                type_report[col] = "mixed (likely numeric with errors)"
            else:
                type_report[col] = "string/categorical"
        else:
            type_report[col] = dtype
    return type_report


def create_data_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a comprehensive data profile including shape,
    missing values, duplicates, and basic statistics.
    """
    profile = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "missing_values": detect_missing_values(df),
        "duplicate_rows": detect_duplicates(df),
        "type_report": detect_invalid_types(df),
        "numeric_summary": {},
    }

    # Add basic statistics for numeric columns
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols:
        desc = df[numeric_cols].describe().to_dict()
        profile["numeric_summary"] = {
            col: {k: round(v, 2) for k, v in stats.items()}
            for col, stats in desc.items()
        }

    return profile
