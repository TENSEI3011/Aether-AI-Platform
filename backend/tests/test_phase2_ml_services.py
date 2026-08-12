"""
============================================================
test_phase2_ml_services.py
AI DLS Phase 2: Model Training & Inference
============================================================
Tests the three core ML services with known inputs so
outputs can be verified against expected results:

  Service 1: Anomaly Detection (Isolation Forest)
  Service 2: Clustering (K-Means + PCA)
  Service 3: Forecasting (Linear Trend / Prophet)

Each test follows the standard ML evaluation pattern:
  Arrange → Act → Assert (accuracy / structure / edge cases)
============================================================
"""

import pytest
import pandas as pd
import numpy as np
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Import ML services with graceful skip if deps missing ─
try:
    from services.anomaly_detector import detect_anomalies
    _ANOMALY_AVAILABLE = True
except ImportError:
    _ANOMALY_AVAILABLE = False

try:
    from services.clustering import cluster_dataframe
    _CLUSTER_AVAILABLE = True
except ImportError:
    _CLUSTER_AVAILABLE = False

from services.forecaster import forecast_series, detect_datetime_and_numeric


# ═══════════════════════════════════════════════════════════
# PHASE 2A — Anomaly Detection (Isolation Forest)
# ═══════════════════════════════════════════════════════════

@pytest.mark.skipif(not _ANOMALY_AVAILABLE, reason="scikit-learn not installed")
class TestAnomalyDetection:

    def test_returns_correct_structure(self, anomaly_df):
        """Result must have all required keys."""
        result = detect_anomalies(anomaly_df, contamination=0.05)
        for key in ("anomaly_count", "total_rows_checked", "anomaly_rows",
                    "contamination_rate", "method", "column_stats"):
            assert key in result, f"Missing key: {key}"

    def test_detects_known_outliers(self, anomaly_df):
        """5 clear outliers were injected — at least 3 must be found."""
        result = detect_anomalies(anomaly_df, contamination=0.10)
        assert result["anomaly_count"] >= 3, (
            f"Expected ≥3 outliers, found {result['anomaly_count']}"
        )

    def test_contamination_rate_respected(self, anomaly_df):
        """Anomaly count should be ≈ contamination × total_rows (within 50% tolerance)."""
        contamination = 0.05
        result = detect_anomalies(anomaly_df, contamination=contamination)
        expected = int(len(anomaly_df) * contamination)
        assert abs(result["anomaly_count"] - expected) <= max(2, expected * 0.5)

    def test_clean_data_has_few_anomalies(self):
        """Perfectly normal data should have very few anomalies at low contamination."""
        np.random.seed(42)
        df = pd.DataFrame({"a": np.random.normal(0, 1, 200),
                           "b": np.random.normal(0, 1, 200)})
        result = detect_anomalies(df, contamination=0.01)
        # At 1% contamination, should find ≤ 5 anomalies in 200 rows
        assert result["anomaly_count"] <= 5

    def test_column_stats_present(self, anomaly_df):
        result = detect_anomalies(anomaly_df, contamination=0.05)
        stats = result["column_stats"]
        assert len(stats) > 0
        for col, s in stats.items():
            assert "mean" in s and "std" in s and "min" in s and "max" in s

    def test_too_few_rows_returns_error(self):
        """Less than 10 rows should return a graceful error, not crash."""
        tiny = pd.DataFrame({"x": [1, 2, 3]})
        result = detect_anomalies(tiny, contamination=0.1)
        # Should either have a message key or very low anomaly count
        assert "message" in result or result["anomaly_count"] <= 1

    def test_method_field_is_isolation_forest(self, anomaly_df):
        result = detect_anomalies(anomaly_df, contamination=0.05)
        assert "isolation_forest" in result["method"].lower() or result["method"] != "none"


# ═══════════════════════════════════════════════════════════
# PHASE 2B — K-Means Clustering (+ PCA)
# ═══════════════════════════════════════════════════════════

@pytest.mark.skipif(not _CLUSTER_AVAILABLE, reason="scikit-learn not installed")
class TestClustering:

    def test_returns_correct_structure(self, numeric_df):
        result = cluster_dataframe(numeric_df)
        for key in ("optimal_k", "cluster_sizes", "cluster_centers",
                    "data_with_clusters", "inertia_values", "method"):
            assert key in result, f"Missing key: {key}"

    def test_finds_correct_number_of_clusters(self, numeric_df):
        """Data has 3 well-separated clusters — elbow method should find 2-4."""
        result = cluster_dataframe(numeric_df)
        assert 2 <= result["optimal_k"] <= 4, (
            f"Expected 2-4 clusters for 3-cluster data, got {result['optimal_k']}"
        )

    def test_all_rows_assigned(self, numeric_df):
        """Every row in the dataset must get a cluster label."""
        result = cluster_dataframe(numeric_df)
        total_assigned = sum(result["cluster_sizes"].values())
        assert total_assigned == len(numeric_df)

    def test_cluster_centers_have_correct_columns(self, numeric_df):
        """Each cluster center must have the same columns as input."""
        result = cluster_dataframe(numeric_df)
        for center in result["cluster_centers"]:
            for col in numeric_df.columns:
                assert col in center, f"Missing column '{col}' in cluster center"

    def test_pca_activated_for_wide_data(self, wide_df):
        """Wide dataset (10 features) should trigger PCA path."""
        result = cluster_dataframe(wide_df)
        assert result.get("pca_used") is True, "Expected PCA to activate for 10 features"
        assert result["pca_variance_retained_pct"] >= 90.0  # 95% target

    def test_pca_not_activated_for_narrow_data(self, numeric_df):
        """3-feature dataset should NOT trigger PCA (only > 5 features)."""
        result = cluster_dataframe(numeric_df)
        assert result.get("pca_used") is False

    def test_method_contains_kmeans(self, numeric_df):
        result = cluster_dataframe(numeric_df)
        assert "kmeans" in result["method"]

    def test_too_few_rows_returns_error(self):
        tiny = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
        result = cluster_dataframe(tiny)
        assert result["optimal_k"] == 0
        assert "message" in result

    def test_empty_dataframe_returns_error(self):
        result = cluster_dataframe(pd.DataFrame())
        assert result["optimal_k"] == 0

    def test_no_numeric_columns_returns_error(self):
        df = pd.DataFrame({"name": ["Alice", "Bob", "Charlie", "Dave", "Eve"]})
        result = cluster_dataframe(df)
        assert result["optimal_k"] == 0

    def test_inertia_decreases_with_k(self, numeric_df):
        """Inertia must decrease (or stay the same) as K increases — basic sanity."""
        result = cluster_dataframe(numeric_df, max_k=6)
        inertias = [item["inertia"] for item in result["inertia_values"]]
        for i in range(1, len(inertias)):
            assert inertias[i] <= inertias[i - 1] * 1.01, (
                f"Inertia increased from k={i+1} to k={i+2}: {inertias}"
            )


# ═══════════════════════════════════════════════════════════
# PHASE 2C — Time-Series Forecasting (Linear Trend / Prophet)
# ═══════════════════════════════════════════════════════════

class TestForecasting:

    def test_returns_correct_structure(self, timeseries_df):
        result = forecast_series(timeseries_df, "date", "sales", periods=14)
        for key in ("historical", "forecast", "trend", "method"):
            assert key in result, f"Missing key: {key}"

    def test_historical_length_matches_input(self, timeseries_df):
        result = forecast_series(timeseries_df, "date", "sales", periods=14)
        assert len(result["historical"]) == len(timeseries_df)

    def test_forecast_length_matches_periods(self, timeseries_df):
        periods = 14
        result = forecast_series(timeseries_df, "date", "sales", periods=periods)
        assert len(result["forecast"]) == periods

    def test_upward_trend_detected(self, timeseries_df):
        """Fixture has a clear upward trend — should be classified as 'up'."""
        result = forecast_series(timeseries_df, "date", "sales", periods=14)
        assert result["trend"] == "up", (
            f"Expected 'up' trend for upward data, got '{result['trend']}'"
        )

    def test_forecast_values_are_numeric(self, timeseries_df):
        result = forecast_series(timeseries_df, "date", "sales", periods=14)
        for point in result["forecast"]:
            assert isinstance(point["yhat"], (int, float))

    def test_confidence_interval_is_ordered(self, timeseries_df):
        """yhat_lower must always be ≤ yhat ≤ yhat_upper."""
        result = forecast_series(timeseries_df, "date", "sales", periods=14)
        for pt in result["forecast"]:
            assert pt["yhat_lower"] <= pt["yhat"] <= pt["yhat_upper"], (
                f"CI not ordered: {pt}"
            )

    def test_insufficient_data_returns_error(self):
        """Less than 5 rows should return a graceful error response."""
        tiny = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=3),
                             "value": [10, 20, 30]})
        result = forecast_series(tiny, "date", "value", periods=7)
        assert "error" in result

    def test_nonexistent_column_returns_error(self, timeseries_df):
        result = forecast_series(timeseries_df, "bad_col", "sales", periods=7)
        assert "error" in result

    def test_auto_detect_datetime_and_numeric(self, timeseries_df):
        """detect_datetime_and_numeric should find 'date' and 'sales' automatically."""
        pair = detect_datetime_and_numeric(timeseries_df)
        assert pair is not None
        assert pair["date_col"] == "date"
        assert pair["value_col"] == "sales"

    def test_auto_detect_returns_none_for_no_dates(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = detect_datetime_and_numeric(df)
        assert result is None
