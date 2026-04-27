"""
============================================================
Core Unit Tests — Validates critical pipeline components
============================================================
Tests:
  - Query Validator (syntax, blocked patterns, schema checks)
  - Query Executor (safety, execution, timeout)
  - Schema Extractor (column type detection)
  - Forecaster (linear and moving average)
============================================================
"""

import pytest
import pandas as pd


# ── Query Validator Tests ─────────────────────────────────

class TestQueryValidator:
    """Tests for services.query_validator"""

    def test_valid_syntax(self):
        from services.query_validator import validate_syntax
        ok, err = validate_syntax("df.head(10)")
        assert ok is True
        assert err == ""

    def test_invalid_syntax(self):
        from services.query_validator import validate_syntax
        ok, err = validate_syntax("df.head(")
        assert ok is False
        assert "Syntax error" in err

    def test_blocked_import(self):
        from services.query_validator import check_blocked_patterns
        safe, violations = check_blocked_patterns("import os")
        assert safe is False
        assert len(violations) > 0

    def test_blocked_exec(self):
        from services.query_validator import check_blocked_patterns
        safe, violations = check_blocked_patterns("exec('print(1)')")
        assert safe is False

    def test_drop_regex_allows_dropna(self):
        """Gap 5: dropna should NOT be blocked by the drop regex."""
        from services.query_validator import check_blocked_patterns
        safe, _ = check_blocked_patterns("df.dropna()")
        assert safe is True

    def test_drop_regex_allows_drop_duplicates(self):
        """Gap 5: drop_duplicates should NOT be blocked."""
        from services.query_validator import check_blocked_patterns
        safe, _ = check_blocked_patterns("df.drop_duplicates()")
        assert safe is True

    def test_drop_regex_blocks_dot_drop(self):
        """Gap 5: df.drop() SHOULD be blocked."""
        from services.query_validator import check_blocked_patterns
        safe, _ = check_blocked_patterns("df.drop(columns=['x'])")
        assert safe is False

    def test_allowed_pandas_ops(self):
        from services.query_validator import validate_query
        result = validate_query("df.groupby('city')['sales'].mean()", ["city", "sales"])
        assert result["is_valid"] is True

    def test_schema_consistency_warning(self):
        from services.query_validator import validate_query
        result = validate_query("df['nonexistent'].mean()", ["city", "sales"])
        assert result["is_valid"] is True  # warnings only, not blocking
        assert len(result["warnings"]) > 0


# ── Query Executor Tests ──────────────────────────────────

class TestQueryExecutor:
    """Tests for services.query_executor"""

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "city": ["A", "B", "C", "A", "B"],
            "sales": [100, 200, 300, 150, 250],
        })

    def test_simple_execution(self, sample_df):
        from services.query_executor import execute_query
        result = execute_query(sample_df, "df.head(3)")
        assert result["success"] is True
        assert result["row_count"] == 3

    def test_groupby_execution(self, sample_df):
        from services.query_executor import execute_query
        result = execute_query(sample_df, "df.groupby('city')['sales'].mean()")
        assert result["success"] is True
        assert result["row_count"] == 3  # A, B, C

    def test_scalar_result(self, sample_df):
        from services.query_executor import execute_query
        result = execute_query(sample_df, "df['sales'].sum()")
        assert result["success"] is True
        assert float(result["data"][0]["value"]) == 1000

    def test_blocks_dunder_access(self, sample_df):
        """Gap 1: Should block __class__ attribute access."""
        from services.query_executor import execute_query
        result = execute_query(sample_df, "().__class__.__mro__[1].__subclasses__()")
        assert result["success"] is False
        assert "Security" in result["error"] or "Blocked" in result["error"]

    def test_blocks_import(self, sample_df):
        """Gap 1: Should block import statements."""
        from services.query_executor import execute_query
        # Multi-line code with import
        result = execute_query(sample_df, "__import__('os').system('ls')")
        assert result["success"] is False

    def test_original_df_not_mutated(self, sample_df):
        """Executor should work on a copy, not mutate original."""
        from services.query_executor import execute_query
        original_len = len(sample_df)
        execute_query(sample_df, "df.head(1)")
        assert len(sample_df) == original_len


# ── Schema Extractor Tests ────────────────────────────────

class TestSchemaExtractor:
    """Tests for services.schema_extractor"""

    def test_extract_schema(self):
        from services.schema_extractor import extract_schema
        df = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [25, 30],
            "score": [95.5, 88.0],
        })
        schema = extract_schema(df)
        assert "columns" in schema
        assert len(schema["columns"]) == 3

        # Check types are detected
        types = {col["name"]: col["semantic_type"] for col in schema["columns"]}
        assert types["name"] == "categorical"
        assert types["age"] == "numeric"
        assert types["score"] == "numeric"

    def test_generate_schema_summary(self):
        from services.schema_extractor import extract_schema, generate_schema_summary
        df = pd.DataFrame({"x": [1, 2], "y": ["a", "b"]})
        schema = extract_schema(df)
        summary = generate_schema_summary(schema)
        assert "x" in summary
        assert "y" in summary
        assert "numeric" in summary
        assert "categorical" in summary


# ── Forecaster Tests ──────────────────────────────────────

class TestForecaster:
    """Tests for services.forecaster"""

    @pytest.fixture
    def sample_data(self):
        return [
            {"year": "2020", "revenue": 100},
            {"year": "2021", "revenue": 120},
            {"year": "2022", "revenue": 140},
            {"year": "2023", "revenue": 160},
            {"year": "2024", "revenue": 180},
        ]

    def test_linear_forecast(self, sample_data):
        from services.forecaster import forecast
        result = forecast(sample_data, "year", "revenue", periods=3, method="linear")
        assert "error" not in result
        assert result["trend"] == "rising"
        assert len(result["forecast"]) == 3
        assert result["confidence"] > 0.9  # Perfect linear data

    def test_moving_average_forecast(self, sample_data):
        from services.forecaster import forecast
        result = forecast(sample_data, "year", "revenue", periods=3, method="moving_average")
        assert "error" not in result
        assert len(result["forecast"]) == 3
        assert result["trend"] in ("rising", "stable", "falling")

    def test_forecast_missing_column(self, sample_data):
        from services.forecaster import forecast
        result = forecast(sample_data, "year", "nonexistent", periods=3)
        assert "error" in result

    def test_forecast_too_few_points(self):
        from services.forecaster import forecast
        data = [{"x": "1", "y": 10}, {"x": "2", "y": 20}]
        result = forecast(data, "x", "y", periods=3)
        assert "error" in result  # Need at least 3 data points
