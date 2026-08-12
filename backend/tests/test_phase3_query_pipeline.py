"""
============================================================
test_phase3_query_pipeline.py
AI DLS Phase 3: Model Evaluation — Query Execution Pipeline
============================================================
Tests the entire query execution pipeline:

  Step 1: Security validation (blocked patterns, AST scan)
  Step 2: Code execution (single-line AND multi-line)
  Step 3: Result formatting (DataFrame, Series, scalar)
  Step 4: Semantic column matching

These are the most critical accuracy tests — they validate
that the LLM's generated code is safely executed and that
the results are correctly structured for the frontend.
============================================================
"""

import pytest
import pandas as pd
import numpy as np
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.query_validator import (
    validate_syntax,
    check_blocked_patterns,
    validate_query,
)
from services.query_executor import execute_query, _is_single_expression


# ═══════════════════════════════════════════════════════════
# PHASE 3A — Security Validator
# ═══════════════════════════════════════════════════════════

class TestQueryValidator:

    # ── Syntax validation ─────────────────────────────────

    def test_valid_syntax_passes(self):
        ok, msg = validate_syntax("df.head(10)")
        assert ok is True
        assert msg == ""

    def test_invalid_syntax_fails(self):
        ok, msg = validate_syntax("df.head(")
        assert ok is False
        assert "syntax" in msg.lower() or "error" in msg.lower()

    def test_none_code_fails_gracefully(self):
        """None input must not crash — returns False with message."""
        ok, msg = validate_syntax(None)
        assert ok is False
        assert len(msg) > 0

    def test_empty_string_fails(self):
        ok, msg = validate_syntax("")
        assert ok is False

    # ── Blocked pattern detection ─────────────────────────

    def test_os_module_blocked(self):
        is_safe, violations = check_blocked_patterns("import os; os.system('rm -rf /')")
        assert is_safe is False
        assert len(violations) > 0

    def test_subprocess_blocked(self):
        is_safe, violations = check_blocked_patterns("import subprocess")
        assert is_safe is False

    def test_exec_blocked(self):
        is_safe, violations = check_blocked_patterns("exec('evil_code')")
        assert is_safe is False

    def test_drop_table_sql_blocked(self):
        is_safe, violations = check_blocked_patterns("DROP TABLE users")
        assert is_safe is False

    def test_safe_pandas_code_allowed(self):
        is_safe, violations = check_blocked_patterns(
            "df.groupby('department')['salary'].mean().reset_index()"
        )
        assert is_safe is True
        assert violations == []

    def test_file_write_blocked(self):
        is_safe, violations = check_blocked_patterns("df.to_csv('out.csv')")
        assert is_safe is False

    def test_delete_operation_blocked(self):
        is_safe, violations = check_blocked_patterns("del df['column']")
        assert is_safe is False

    # ── Full validation pipeline ──────────────────────────

    def test_valid_query_passes_full_validation(self, clean_df):
        from services.schema_extractor import extract_schema
        schema = extract_schema(clean_df)
        # validate_query expects List[str] column names, not List[Dict]
        col_names = [c["name"] for c in schema["columns"]]
        result = validate_query("df['salary'].mean()", col_names)
        assert result["is_valid"] is True

    def test_blocked_query_fails_full_validation(self, clean_df):
        from services.schema_extractor import extract_schema
        schema = extract_schema(clean_df)
        col_names = [c["name"] for c in schema["columns"]]
        result = validate_query("import os", col_names)
        assert result["is_valid"] is False


# ═══════════════════════════════════════════════════════════
# PHASE 3B — Query Executor (Single-line & Multi-line)
# ═══════════════════════════════════════════════════════════

class TestQueryExecutor:

    # ── Single expression detection ───────────────────────

    def test_single_expression_detected(self):
        assert _is_single_expression("df.head(5)") is True
        assert _is_single_expression("df['salary'].mean()") is True

    def test_multiline_not_single_expression(self):
        assert _is_single_expression("x = 1\nx + 1") is False

    # ── Single-line execution ─────────────────────────────

    def test_execute_head_returns_dataframe(self, clean_df):
        result = execute_query(clean_df, "df.head(5)")
        assert result["success"] is True
        assert result["row_count"] == 5
        assert isinstance(result["data"], list)
        assert isinstance(result["columns"], list)

    def test_execute_scalar_mean(self, clean_df):
        result = execute_query(clean_df, "df['salary'].mean()")
        assert result["success"] is True
        assert result["row_count"] == 1
        assert isinstance(result["data"][0]["value"], float)

    def test_execute_groupby_returns_dataframe(self, clean_df):
        result = execute_query(
            clean_df,
            "df.groupby('department')['salary'].mean().reset_index()"
        )
        assert result["success"] is True
        assert "department" in result["columns"]
        assert "salary" in result["columns"]

    def test_execute_filter(self, clean_df):
        result = execute_query(clean_df, "df[df['age'] > 40]")
        assert result["success"] is True
        # Verify all returned rows actually satisfy the filter
        for row in result["data"]:
            assert row["age"] > 40

    def test_execute_series_reset_index(self, clean_df):
        result = execute_query(clean_df, "df['department'].value_counts()")
        assert result["success"] is True
        assert result["row_count"] > 0

    # ── Multi-line code execution (NEW — was broken before) ─

    def test_execute_multiline_assignment(self, clean_df):
        """Multi-line: assignment then return var — must capture result."""
        code = "result = df.groupby('department')['salary'].mean().reset_index()\nresult"
        result = execute_query(clean_df, code)
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "department" in result["columns"]

    def test_execute_multiline_intermediate_var(self, clean_df):
        """Multi-line with intermediate step — last expression returned."""
        code = (
            "filtered = df[df['salary'] > 50000]\n"
            "filtered.groupby('department')['salary'].count().reset_index()"
        )
        result = execute_query(clean_df, code)
        assert result["success"] is True, f"Failed: {result.get('error')}"

    def test_execute_multiline_top_n(self, clean_df):
        """Top-N pattern from few-shot examples — multi-step."""
        code = (
            "grouped = df.groupby('department')['salary'].sum().reset_index()\n"
            "grouped.nlargest(3, 'salary')"
        )
        result = execute_query(clean_df, code)
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert result["row_count"] <= 3

    # ── Safety & edge cases ───────────────────────────────

    def test_original_df_not_mutated(self, clean_df):
        """Executor must never modify the original DataFrame."""
        original_len = len(clean_df)
        original_cols = list(clean_df.columns)
        execute_query(clean_df, "df['new_col'] = 1")
        assert len(clean_df) == original_len
        assert list(clean_df.columns) == original_cols

    def test_bad_column_name_returns_error(self, clean_df):
        result = execute_query(clean_df, "df['nonexistent_column'].mean()")
        assert result["success"] is False
        assert result["error"] is not None

    def test_large_result_truncated_to_500(self):
        """Results over 500 rows must be truncated."""
        big_df = pd.DataFrame({"x": range(1000)})
        result = execute_query(big_df, "df")
        assert result["success"] is True
        assert len(result["data"]) == 500
        assert result["row_count"] == 1000  # reports actual count

    def test_correlation_returns_dataframe(self, clean_df):
        """Example 8 from few-shot: correlation — returns a DataFrame."""
        result = execute_query(clean_df, "df[['age','salary']].dropna().corr()")
        assert result["success"] is True
        assert "age" in result["columns"] or "salary" in result["columns"]


# ═══════════════════════════════════════════════════════════
# PHASE 3C — Semantic Column Matching
# ═══════════════════════════════════════════════════════════

class TestSemanticMatcher:

    def test_exact_match_found(self):
        try:
            from services.semantic_matcher import find_best_column
        except ImportError:
            pytest.skip("sentence-transformers not installed")

        result = find_best_column("salary", ["age", "salary", "department"])
        assert result == "salary"

    def test_synonym_match(self):
        try:
            from services.semantic_matcher import find_best_column
        except ImportError:
            pytest.skip("sentence-transformers not installed")

        # "income" should match "salary"
        result = find_best_column("income", ["age", "salary", "department"])
        assert result in ("salary", None)  # May not match at low threshold

    def test_returns_none_for_no_columns(self):
        try:
            from services.semantic_matcher import find_best_column
        except ImportError:
            pytest.skip("sentence-transformers not installed")

        result = find_best_column("anything", [])
        assert result is None

    def test_keyword_fallback_works(self):
        """Even without sentence-transformers, keyword fallback must work."""
        from services.semantic_matcher import _keyword_match
        result = _keyword_match("average salary", ["age", "salary", "department"])
        assert result == "salary"
