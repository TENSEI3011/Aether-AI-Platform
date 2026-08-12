"""
============================================================
Data Validator — Validates and auto-cleans uploaded datasets
============================================================
Checks file format, detects missing values, duplicates,
invalid types, and generates a data profile summary.

ENHANCEMENT: auto_clean_dataframe() now runs on every upload.
  - Strips whitespace from column names ("PM 2.5 " → "PM_2.5")
  - Converts numeric-looking string columns to float
  - Parses date-like string columns to datetime
  - Cleans string values (strip whitespace)
  - Deduplicates rows
============================================================
"""

import pandas as pd
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def auto_clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Automatically clean a DataFrame on upload.

    Cleans:
      1. Column names: strip whitespace, replace spaces with underscores
      2. Numeric strings: "1,234.5" or " 88.3 " → 88.3 (float)
      3. Date strings: auto-parse columns that look like dates
      4. String values: strip leading/trailing whitespace
      5. Duplicate rows: remove exact duplicates

    ML Concept: Data Preprocessing Pipeline — clean data dramatically
    improves LLM code generation accuracy (correct column names,
    correct types) and downstream analysis results.

    Returns:
        Cleaned copy of the DataFrame.
    """
    df = df.copy()

    # ── 1. Clean column names ─────────────────────────────
    cleaned_cols = []
    for col in df.columns:
        # Strip and normalise spaces
        clean = str(col).strip()
        # Replace sequences of whitespace/special chars with underscores
        clean = re.sub(r"[\s\-/\\]+", "_", clean)
        # Remove any remaining non-alphanumeric except _ and .
        clean = re.sub(r"[^\w\.]", "", clean)
        cleaned_cols.append(clean)
    df.columns = cleaned_cols

    # ── 2. Convert numeric-looking object columns ─────────
    for col in df.select_dtypes(include=["object"]).columns:
        # Remove commas from numbers like "1,234.5"
        try:
            stripped = df[col].dropna().astype(str).str.strip()
            numeric_attempt = stripped.str.replace(",", "", regex=False)
            converted = pd.to_numeric(numeric_attempt, errors="coerce")
            non_null_orig = df[col].notna().sum()
            if non_null_orig > 0 and converted.notna().sum() / non_null_orig > 0.85:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.strip().str.replace(",", "", regex=False),
                    errors="coerce",
                )
                logger.info("DataCleaner: Converted '%s' to numeric", col)
        except Exception:
            pass

    # ── 3. Parse date-like string columns ─────────────────
    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna().head(30)
        try:
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().sum() / max(len(sample), 1) > 0.8:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                logger.info("DataCleaner: Parsed '%s' as datetime", col)
        except Exception:
            pass

    # ── 4. Strip whitespace from string values ────────────
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip().replace("nan", pd.NA)

    # ── 5. Remove duplicate rows ──────────────────────────
    n_dupes = df.duplicated().sum()
    if n_dupes > 0:
        df = df.drop_duplicates()
        logger.info("DataCleaner: Removed %d duplicate rows", n_dupes)

    return df


def validate_file_format(filename: str) -> bool:
    """Check that uploaded file is CSV or Excel."""
    allowed = (".csv", ".xlsx", ".xls")
    return any(filename.lower().endswith(ext) for ext in allowed)


def load_dataframe(filepath: str, apply_cleaning: bool = True) -> pd.DataFrame:
    """
    Load a CSV or Excel file into a Pandas DataFrame.
    Applies auto-cleaning by default (improves LLM accuracy).
    Raises ValueError if the file format is unsupported.

    Parameters:
        filepath:       Path to the file
        apply_cleaning: If True, runs auto_clean_dataframe() after loading
    """
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    elif filepath.endswith((".xlsx", ".xls")):
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}")

    if apply_cleaning:
        df = auto_clean_dataframe(df)

    return df


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
