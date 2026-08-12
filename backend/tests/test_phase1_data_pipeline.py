"""
============================================================
test_phase1_data_pipeline.py
AI DLS Phase 1: Data Collection & Validation
============================================================
Tests the full data ingestion pipeline:
  - File loading (CSV, Excel, bad formats)
  - Data profiling (rows, cols, nulls, duplicates)
  - Schema extraction + column type classification
  - ID column and binary flag detection (new)
  - Schema summary for LLM context
============================================================
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.data_validator import load_dataframe, create_data_profile, validate_file_format
from services.schema_extractor import (
    classify_column_type,
    extract_schema,
    generate_schema_summary,
)


# ═══════════════════════════════════════════════════════════
# PHASE 1A — File Loading & Format Validation
# ═══════════════════════════════════════════════════════════

class TestFileLoading:

    def test_validate_csv_format(self):
        assert validate_file_format("data.csv") is True

    def test_validate_xlsx_format(self):
        assert validate_file_format("data.xlsx") is True

    def test_validate_xls_format(self):
        assert validate_file_format("data.xls") is True

    def test_reject_txt_format(self):
        assert validate_file_format("data.txt") is False

    def test_reject_json_format(self):
        assert validate_file_format("data.json") is False

    def test_reject_no_extension(self):
        assert validate_file_format("datafile") is False

    def test_load_csv_file(self, clean_df, tmp_path):
        """Test that a saved CSV can be loaded back correctly."""
        path = str(tmp_path / "test.csv")
        clean_df.to_csv(path, index=False)
        loaded = load_dataframe(path)
        assert isinstance(loaded, pd.DataFrame)
        assert len(loaded) == len(clean_df)
        assert list(loaded.columns) == list(clean_df.columns)

    def test_load_excel_file(self, clean_df, tmp_path):
        """Test that a saved Excel file can be loaded back correctly."""
        path = str(tmp_path / "test.xlsx")
        clean_df.to_excel(path, index=False)
        loaded = load_dataframe(path)
        assert isinstance(loaded, pd.DataFrame)
        assert len(loaded) == len(clean_df)

    def test_load_missing_file_raises(self):
        """Loading a non-existent file must raise an exception."""
        with pytest.raises(Exception):
            load_dataframe("/nonexistent/path/file.csv")


# ═══════════════════════════════════════════════════════════
# PHASE 1B — Data Profiling
# ═══════════════════════════════════════════════════════════

class TestDataProfiling:

    def test_profile_row_count(self, clean_df):
        profile = create_data_profile(clean_df)
        assert profile["rows"] == 100

    def test_profile_column_count(self, clean_df):
        profile = create_data_profile(clean_df)
        assert profile["columns"] == len(clean_df.columns)

    def test_profile_no_nulls_in_clean_data(self, clean_df):
        profile = create_data_profile(clean_df)
        assert all(v == 0 for v in profile["missing_values"].values())

    def test_profile_detects_nulls(self, dirty_df):
        profile = create_data_profile(dirty_df)
        total_missing = sum(profile["missing_values"].values())
        assert total_missing > 0, "Expected nulls in dirty_df to be detected"

    def test_profile_detects_duplicates(self, dirty_df):
        """dirty_df has 2 identical Alice rows → 1 duplicate."""
        profile = create_data_profile(dirty_df)
        assert profile["duplicate_rows"] >= 1

    def test_profile_no_duplicates_in_clean(self, clean_df):
        profile = create_data_profile(clean_df)
        assert profile["duplicate_rows"] == 0

    def test_profile_returns_dict(self, clean_df):
        profile = create_data_profile(clean_df)
        assert isinstance(profile, dict)
        assert "rows" in profile and "columns" in profile


# ═══════════════════════════════════════════════════════════
# PHASE 1C — Schema Extraction & Column Classification
# ═══════════════════════════════════════════════════════════

class TestColumnClassification:

    def test_numeric_column(self):
        # Use total_rows=0 to skip ID-column heuristic (heuristic only fires when total_rows > 0)
        s = pd.Series([1.0, 2.5, 3.1, 4.7, 5.2, 3.1, 2.5])  # repeated values → NOT an ID
        assert classify_column_type(s, total_rows=7) == "numeric"

    def test_categorical_column(self):
        s = pd.Series(["cat", "dog", "bird", "cat", "dog"])
        assert classify_column_type(s, total_rows=5) == "categorical"

    def test_boolean_column_native(self):
        s = pd.Series([True, False, True, False])
        assert classify_column_type(s, total_rows=4) == "boolean"

    def test_binary_flag_detected(self):
        """0/1 integer column should be classified as boolean, not numeric."""
        s = pd.Series([0, 1, 0, 1, 1, 0])
        result = classify_column_type(s, total_rows=6)
        assert result == "boolean", f"Expected 'boolean' but got '{result}'"

    def test_id_column_detected(self):
        """Column where every value is unique should be classified as 'id'."""
        n = 100
        s = pd.Series(range(1, n + 1), dtype=float)
        result = classify_column_type(s, total_rows=n)
        assert result == "id", f"Expected 'id' but got '{result}'"

    def test_datetime_column_string(self):
        """String dates with high parse rate should be detected as datetime."""
        s = pd.Series(["2023-01-01", "2023-01-02", "2023-01-03",
                       "2023-01-04", "2023-01-05"] * 6)
        result = classify_column_type(s, total_rows=30)
        assert result == "datetime", f"Expected 'datetime' but got '{result}'"

    def test_string_column_not_misclassified_as_datetime(self):
        """Generic strings like category names should NOT be datetime."""
        s = pd.Series(["Engineering", "Sales", "HR", "Finance"] * 5)
        result = classify_column_type(s, total_rows=20)
        assert result == "categorical"

    def test_schema_structure(self, clean_df):
        schema = extract_schema(clean_df)
        assert "total_rows" in schema
        assert "total_columns" in schema
        assert "columns" in schema
        assert schema["total_rows"] == len(clean_df)
        assert schema["total_columns"] == len(clean_df.columns)

    def test_schema_has_numeric_stats(self, clean_df):
        """Numeric columns should have min, max, mean in schema."""
        schema = extract_schema(clean_df)
        numeric_cols = [c for c in schema["columns"] if c["semantic_type"] == "numeric"]
        assert len(numeric_cols) > 0
        for col in numeric_cols:
            assert "min" in col and "max" in col and "mean" in col

    def test_schema_has_top_values_for_categorical(self, clean_df):
        """Categorical columns should have top_values in schema."""
        schema = extract_schema(clean_df)
        cat_cols = [c for c in schema["columns"] if c["semantic_type"] == "categorical"]
        assert len(cat_cols) > 0
        for col in cat_cols:
            assert "top_values" in col

    def test_schema_summary_non_empty(self, clean_df):
        schema = extract_schema(clean_df)
        summary = generate_schema_summary(schema)
        assert isinstance(summary, str)
        assert len(summary) > 50

    def test_schema_summary_id_column_annotated(self, clean_df):
        """ID columns must have 'do NOT aggregate' note in summary."""
        schema = extract_schema(clean_df)
        summary = generate_schema_summary(schema)
        assert "do NOT aggregate" in summary or "identifier" in summary.lower()
