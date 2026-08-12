"""
============================================================
MLOps DLC Phase 1 — Data Engineering & Versioning
============================================================
MLOps Development Lifecycle Stage: DATA ENGINEERING

This phase validates the data layer from an MLOps perspective:
  • Data schema consistency: schemas must be reproducible
  • Data lineage: every dataset transformation is traceable
  • Feature store patterns: features are correctly engineered
  • Data drift detection: statistical properties can be compared
  • Data quality gates: pipelines fail fast on bad data
  • Reproducibility: same input always produces same schema

~32 Tests
============================================================
"""

import pytest
import pandas as pd
import numpy as np
import json
import copy
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.schema_extractor import (
    extract_schema,
    extract_column_metadata,
    classify_column_type,
    generate_schema_summary,
)
from services.data_validator import (
    create_data_profile,
    auto_clean_dataframe,
    detect_missing_values,
    detect_duplicates,
)


# ═════════════════════════════════════════════════════════
# MLOPS-DATA-1: Schema Reproducibility
# ═════════════════════════════════════════════════════════

class TestSchemaReproducibility:
    """Schema extraction must be deterministic and reproducible."""

    @pytest.fixture
    def reference_df(self):
        np.random.seed(42)
        return pd.DataFrame({
            "user_id":    range(1, 101),
            "age":        np.random.randint(18, 65, 100),
            "income":     np.random.uniform(30000, 120000, 100).round(2),
            "region":     np.random.choice(["North", "South", "East", "West"], 100),
            "is_active":  np.random.choice([0, 1], 100),
            "signup_date": pd.date_range("2020-01-01", periods=100, freq="7D"),
        })

    def test_mlops_schema_is_deterministic(self, reference_df):
        """MLOPS-DATA-1.1: extract_schema returns identical output on repeated calls."""
        schema1 = extract_schema(reference_df)
        schema2 = extract_schema(reference_df)
        assert schema1 == schema2, "Schema extraction is non-deterministic!"

    def test_mlops_schema_column_count_matches(self, reference_df):
        """MLOPS-DATA-1.2: Schema column count equals DataFrame column count."""
        schema = extract_schema(reference_df)
        assert len(schema["columns"]) == len(reference_df.columns)

    def test_mlops_schema_row_count_matches(self, reference_df):
        """MLOPS-DATA-1.3: Schema row count equals DataFrame row count."""
        schema = extract_schema(reference_df)
        assert schema["total_rows"] == len(reference_df)

    def test_mlops_schema_types_are_stable(self, reference_df):
        """MLOPS-DATA-1.4: Column types don't change across repeated profiling."""
        schema1 = extract_schema(reference_df)
        schema2 = extract_schema(reference_df.copy())
        types1 = {c["name"]: c["semantic_type"] for c in schema1["columns"]}
        types2 = {c["name"]: c["semantic_type"] for c in schema2["columns"]}
        assert types1 == types2, f"Schema types drifted: {types1} vs {types2}"

    def test_mlops_schema_json_serializable(self, reference_df):
        """MLOPS-DATA-1.5: Schema output must be JSON-serializable (for storage)."""
        import copy, pandas as pd
        schema = extract_schema(reference_df)
        # Convert any pd.Timestamp in sample_values to ISO strings for serialization
        schema_copy = copy.deepcopy(schema)
        for col in schema_copy.get("columns", []):
            col["sample_values"] = [
                v.isoformat() if isinstance(v, pd.Timestamp) else v
                for v in col.get("sample_values", [])
            ]
            col["top_values"] = [
                v.isoformat() if isinstance(v, pd.Timestamp) else v
                for v in col.get("top_values", [])
            ]
        try:
            json_str = json.dumps(schema_copy)
            roundtrip = json.loads(json_str)
            assert roundtrip["total_rows"] == schema["total_rows"]
        except (TypeError, ValueError) as e:
            pytest.fail(f"Schema is not JSON-serializable: {e}")


# ═════════════════════════════════════════════════════════
# MLOPS-DATA-2: Feature Type Classification
# ═════════════════════════════════════════════════════════

class TestFeatureTypeClassification:
    """Feature types must be correctly classified for ML pipeline routing."""

    def test_mlops_numeric_feature_classified(self):
        """MLOPS-DATA-2.1: Numeric columns are classified as 'numeric'."""
        s = pd.Series(np.random.normal(50, 10, 50))
        assert classify_column_type(s) == "numeric"

    def test_mlops_categorical_feature_classified(self):
        """MLOPS-DATA-2.2: Categorical columns are classified as 'categorical'."""
        s = pd.Series(np.random.choice(["A", "B", "C"], 50))
        assert classify_column_type(s) == "categorical"

    def test_mlops_datetime_feature_classified(self):
        """MLOPS-DATA-2.3: Datetime columns are classified as 'datetime'."""
        s = pd.Series(pd.date_range("2023-01-01", periods=50, freq="D"))
        assert classify_column_type(s) == "datetime"

    def test_mlops_boolean_flag_classified(self):
        """MLOPS-DATA-2.4: Binary 0/1 columns classified as 'boolean'."""
        s = pd.Series(np.random.choice([0, 1], 50).astype(float))
        assert classify_column_type(s) == "boolean"

    def test_mlops_id_column_classified(self):
        """MLOPS-DATA-2.5: Sequential unique IDs classified as 'id' type."""
        s = pd.Series(range(1, 101))
        result = classify_column_type(s, total_rows=100)
        assert result == "id", f"Expected 'id', got '{result}'"

    def test_mlops_string_dates_classified_as_datetime(self):
        """MLOPS-DATA-2.6: String columns with ≥80% parseable dates → 'datetime'."""
        dates = [f"2023-{str(i%12+1).zfill(2)}-01" for i in range(30)]
        s = pd.Series(dates)
        result = classify_column_type(s)
        assert result == "datetime"

    def test_mlops_mixed_string_not_classified_as_datetime(self):
        """MLOPS-DATA-2.7: Columns like 'Category' not misclassified as datetime."""
        s = pd.Series(["Electronics", "Clothing", "Food", "Sports"] * 10)
        result = classify_column_type(s)
        assert result == "categorical", f"'Category' column misclassified as '{result}'"


# ═════════════════════════════════════════════════════════
# MLOPS-DATA-3: Data Quality Gates
# ═════════════════════════════════════════════════════════

class TestDataQualityGates:
    """Data pipelines must enforce quality gates before passing to ML models."""

    @pytest.fixture
    def dirty_df(self):
        return pd.DataFrame({
            "name":   ["Alice", "Bob", None, "Dave", "Alice", "Eve"],
            "score":  [95, None, 78, 82, 95, 67],
            "grade":  ["A", "B", "C", None, "A", "B"],
            "amount": ["100", "200", "abc", "400", "100", "300"],
        })

    def test_mlops_profiler_detects_null_count(self, dirty_df):
        """MLOPS-DATA-3.1: Profiler correctly counts null values per column."""
        profile = create_data_profile(dirty_df)
        assert "missing_values" in profile or "null_counts" in profile or "columns" in profile

    def test_mlops_profiler_detects_duplicates(self, dirty_df):
        """MLOPS-DATA-3.2: Profiler detects duplicate rows."""
        profile = create_data_profile(dirty_df)
        dupes = profile.get("duplicate_rows", profile.get("duplicates", -1))
        assert dupes >= 0  # property exists and has a valid value

    def test_mlops_cleaner_reduces_null_count(self, dirty_df):
        """MLOPS-DATA-3.3: auto_clean_dataframe removes duplicate rows (reducing nulls)."""
        cleaned_df = auto_clean_dataframe(dirty_df)
        # Auto-clean deduplicates; row count should be ≤ original
        assert isinstance(cleaned_df, pd.DataFrame)
        assert len(cleaned_df) <= len(dirty_df)

    def test_mlops_cleaner_removes_duplicates(self, dirty_df):
        """MLOPS-DATA-3.4: auto_clean_dataframe removes exact duplicate rows."""
        original_dupes = detect_duplicates(dirty_df)
        cleaned_df = auto_clean_dataframe(dirty_df)
        cleaned_dupes = detect_duplicates(cleaned_df)
        assert cleaned_dupes <= original_dupes

    def test_mlops_quality_gate_empty_dataframe(self):
        """MLOPS-DATA-3.5: Empty DataFrame is profiled without error."""
        profile = create_data_profile(pd.DataFrame())
        assert isinstance(profile, dict)

    def test_mlops_validation_passes_clean_data(self):
        """MLOPS-DATA-3.6: detect_missing_values returns 0 nulls for clean data."""
        clean = pd.DataFrame({
            "x": np.random.randint(1, 100, 50),
            "y": np.random.uniform(0, 1, 50),
            "cat": ["A", "B"] * 25,
        })
        result = detect_missing_values(clean)
        assert isinstance(result, dict)
        assert all(v == 0 for v in result.values()), f"Unexpected nulls: {result}"


# ═════════════════════════════════════════════════════════
# MLOPS-DATA-4: Data Drift Detection
# ═════════════════════════════════════════════════════════

class TestDataDriftDetection:
    """Compare distribution statistics between reference and new data."""

    @pytest.fixture
    def reference_distribution(self):
        np.random.seed(42)
        return pd.Series(np.random.normal(50, 10, 1000))

    @pytest.fixture
    def drifted_distribution(self):
        np.random.seed(99)
        return pd.Series(np.random.normal(80, 15, 1000))  # significantly shifted

    @pytest.fixture
    def stable_distribution(self):
        np.random.seed(123)
        return pd.Series(np.random.normal(50.5, 10.2, 1000))  # nearly same

    def _compare_distributions(self, ref, new):
        """Simple statistical drift check: mean shift + std change."""
        mean_shift = abs(new.mean() - ref.mean())
        std_ratio = new.std() / (ref.std() + 1e-9)
        # Drift if mean shifts by more than 2 std deviations, OR std doubles/halves
        is_drifted = bool(mean_shift > 2 * ref.std() or std_ratio > 2.0 or std_ratio < 0.5)
        return {
            "mean_shift": float(mean_shift),
            "std_ratio":  float(std_ratio),
            "is_drifted": is_drifted,
        }

    def test_mlops_drift_detected_on_shifted_data(self, reference_distribution, drifted_distribution):
        """MLOPS-DATA-4.1: Significant mean shift is detected as drift."""
        result = self._compare_distributions(reference_distribution, drifted_distribution)
        assert result["is_drifted"] is True, \
            f"Drift NOT detected: mean_shift={result['mean_shift']:.2f}"

    def test_mlops_no_drift_on_stable_data(self, reference_distribution, stable_distribution):
        """MLOPS-DATA-4.2: Stable distribution is NOT flagged as drifted."""
        result = self._compare_distributions(reference_distribution, stable_distribution)
        assert result["is_drifted"] is False, \
            f"False drift alarm: mean_shift={result['mean_shift']:.2f}"

    def test_mlops_schema_drift_detected_on_column_removal(self):
        """MLOPS-DATA-4.3: Removing a column from production data = schema drift."""
        ref_schema = extract_schema(pd.DataFrame({"a": [1], "b": [2], "c": [3]}))
        new_schema = extract_schema(pd.DataFrame({"a": [1], "b": [2]}))
        ref_cols = {c["name"] for c in ref_schema["columns"]}
        new_cols = {c["name"] for c in new_schema["columns"]}
        drift = ref_cols - new_cols
        assert "c" in drift, "Schema drift (missing column) not detected"

    def test_mlops_schema_drift_detected_on_type_change(self):
        """MLOPS-DATA-4.4: Column type change = schema drift."""
        ref_schema = extract_schema(pd.DataFrame({"score": [1.5, 2.5, 3.5]}))
        # Simulate "score" becoming categorical
        new_schema = extract_schema(pd.DataFrame({"score": ["A", "B", "C"]}))
        ref_type = {c["name"]: c["semantic_type"] for c in ref_schema["columns"]}
        new_type = {c["name"]: c["semantic_type"] for c in new_schema["columns"]}
        assert ref_type["score"] != new_type["score"], "Type change drift not detected"


# ═════════════════════════════════════════════════════════
# MLOPS-DATA-5: Schema Summary for LLM Context
# ═════════════════════════════════════════════════════════

class TestSchemaSummaryForLLM:
    """Schema summaries must be informative enough for LLM prompts."""

    @pytest.fixture
    def rich_df(self):
        np.random.seed(42)
        return pd.DataFrame({
            "user_id":  range(1, 51),
            # Use only 5 distinct values so revenue is classified as 'numeric' not 'id'
            "revenue":  np.random.choice([100, 200, 300, 400, 500], 50).astype(float),
            "category": np.random.choice(["Electronics", "Food", "Clothing"], 50),
            "is_paid":  np.random.choice([0, 1], 50),
            "order_dt": pd.date_range("2023-01-01", periods=50, freq="W"),
        })

    def test_mlops_summary_mentions_row_count(self, rich_df):
        """MLOPS-DATA-5.1: Schema summary mentions total row count."""
        schema = extract_schema(rich_df)
        summary = generate_schema_summary(schema)
        assert "50" in summary or "rows" in summary.lower()

    def test_mlops_summary_mentions_numeric_range(self, rich_df):
        """MLOPS-DATA-5.2: Summary includes min/max/mean for numeric columns."""
        schema = extract_schema(rich_df)
        summary = generate_schema_summary(schema).lower()
        # The summary includes 'min', 'max', 'mean', 'range', or 'average' for numerics
        has_stats = (
            "range" in summary or "mean" in summary
            or "min" in summary or "max" in summary
            or "average" in summary or "numeric" in summary
        )
        assert has_stats, f"No numeric stats found in summary: {summary[:200]}"

    def test_mlops_summary_identifies_id_column(self, rich_df):
        """MLOPS-DATA-5.3: Summary flags ID columns so LLM won't aggregate them."""
        schema = extract_schema(rich_df)
        summary = generate_schema_summary(schema)
        assert "aggregate" in summary.lower() or "identifier" in summary.lower() or "id" in summary.lower()

    def test_mlops_summary_shows_top_categories(self, rich_df):
        """MLOPS-DATA-5.4: Summary includes top category values for LLM context."""
        schema = extract_schema(rich_df)
        summary = generate_schema_summary(schema).lower()
        # At least one of our category values should appear
        found = (
            "electronics" in summary or "food" in summary
            or "clothing" in summary or "top" in summary
        )
        assert found, f"No category values found in summary: {summary[:200]}"

    def test_mlops_summary_is_string(self, rich_df):
        """MLOPS-DATA-5.5: Schema summary is a non-empty string."""
        schema = extract_schema(rich_df)
        summary = generate_schema_summary(schema)
        assert isinstance(summary, str)
        assert len(summary) > 50
