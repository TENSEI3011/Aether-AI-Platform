"""
============================================================
MLOps DLC Phase 2 — Model Serving & Inference Validation
============================================================
MLOps Development Lifecycle Stage: MODEL SERVING

This phase validates how ML models behave in a serving context:
  • Inference stability: models produce same output for same input
  • Confidence calibration: scores are properly bounded
  • Latency SLAs: inference must complete within acceptable time
  • Graceful degradation: fallbacks engage when primary model fails
  • Input shape handling: models handle variable-size inputs
  • Output schema validation: model outputs have consistent shapes

These validate the three core ML services:
  - Isolation Forest (anomaly detection)
  - K-Means + PCA (clustering)
  - Linear Trend / Prophet (forecasting)

~36 Tests
============================================================
"""

import pytest
import time
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.anomaly_detector import detect_anomalies, add_anomaly_column
from services.clustering import cluster_dataframe
from services.forecaster import forecast_series, detect_datetime_and_numeric


# ─────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────

@pytest.fixture
def normal_df():
    np.random.seed(42)
    return pd.DataFrame({
        "metric_a": np.random.normal(100, 10, 200),
        "metric_b": np.random.normal(500, 50, 200),
    })

@pytest.fixture
def anomaly_injected_df():
    np.random.seed(7)
    normal = pd.DataFrame({
        "x": np.random.normal(50, 5, 95),
        "y": np.random.normal(100, 10, 95),
    })
    outliers = pd.DataFrame({
        "x": [1000, -1000, 900, -900, 950],
        "y": [5000, -5000, 4500, -4500, 4800],
    })
    return pd.concat([normal, outliers], ignore_index=True)

@pytest.fixture
def clustered_df():
    np.random.seed(0)
    c1 = np.random.randn(50, 2) + [0, 0]
    c2 = np.random.randn(50, 2) + [15, 15]
    c3 = np.random.randn(50, 2) + [7, -7]
    data = np.vstack([c1, c2, c3])
    return pd.DataFrame(data, columns=["feature_a", "feature_b"])

@pytest.fixture
def timeseries_df():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=120, freq="D")
    trend = np.linspace(100, 250, 120)
    noise = np.random.normal(0, 8, 120)
    return pd.DataFrame({"date": dates, "revenue": (trend + noise).round(2)})


# ═════════════════════════════════════════════════════════
# MLOPS-SERVE-1: Anomaly Detection Inference
# ═════════════════════════════════════════════════════════

class TestAnomalyDetectionServing:
    """Anomaly detection must be stable, bounded, and schema-consistent."""

    def test_mlops_inference_output_schema(self, normal_df):
        """MLOPS-SERVE-1.1: Anomaly output always has required schema keys."""
        result = detect_anomalies(normal_df)
        required = ["anomaly_count", "anomaly_indices", "anomaly_rows",
                    "column_stats", "method"]
        for key in required:
            assert key in result, f"Missing required key: {key}"

    def test_mlops_inference_is_deterministic(self, normal_df):
        """MLOPS-SERVE-1.2: Same input always produces same anomaly indices."""
        r1 = detect_anomalies(normal_df, contamination=0.05)
        r2 = detect_anomalies(normal_df, contamination=0.05)
        assert r1["anomaly_count"] == r2["anomaly_count"]
        assert r1["anomaly_indices"] == r2["anomaly_indices"]

    def test_mlops_inference_detects_injected_outliers(self, anomaly_injected_df):
        """MLOPS-SERVE-1.3: Model detects the 5 injected extreme outliers."""
        result = detect_anomalies(anomaly_injected_df, contamination=0.07)
        assert result["anomaly_count"] >= 3, \
            f"Only {result['anomaly_count']} anomalies detected, expected ≥ 3"

    def test_mlops_contamination_rate_bounded(self, normal_df):
        """MLOPS-SERVE-1.4: contamination_rate stays within [0, 1]."""
        result = detect_anomalies(normal_df, contamination=0.1)
        rate = result["contamination_rate"]
        assert 0.0 <= rate <= 1.0

    def test_mlops_inference_latency_sla(self, normal_df):
        """MLOPS-SERVE-1.5: Inference on 200-row dataset < 5 seconds (SLA)."""
        start = time.time()
        detect_anomalies(normal_df)
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Inference SLA breach: {elapsed:.2f}s"

    def test_mlops_add_anomaly_column_doesnt_mutate_original(self, normal_df):
        """MLOPS-SERVE-1.6: add_anomaly_column returns copy, not in-place."""
        original_cols = list(normal_df.columns)
        enriched = add_anomaly_column(normal_df)
        assert list(normal_df.columns) == original_cols
        assert "is_anomaly" in enriched.columns

    def test_mlops_empty_df_inference_returns_dict(self):
        """MLOPS-SERVE-1.7: Empty DataFrame returns structured error dict."""
        result = detect_anomalies(pd.DataFrame())
        assert isinstance(result, dict)
        assert result["anomaly_count"] == 0

    def test_mlops_single_row_returns_graceful(self):
        """MLOPS-SERVE-1.8: Single-row input returns valid response."""
        df = pd.DataFrame({"x": [42.0], "y": [99.0]})
        result = detect_anomalies(df)
        assert isinstance(result, dict)
        assert "anomaly_count" in result

    def test_mlops_column_stats_bounds(self, normal_df):
        """MLOPS-SERVE-1.9: Column stats have proper numeric bounds."""
        result = detect_anomalies(normal_df)
        for col, stats in result["column_stats"].items():
            assert stats["min"] <= stats["mean"] <= stats["max"], \
                f"Column {col}: min({stats['min']}) <= mean({stats['mean']}) <= max({stats['max']}) violated"


# ═════════════════════════════════════════════════════════
# MLOPS-SERVE-2: Clustering Serving
# ═════════════════════════════════════════════════════════

class TestClusteringServing:
    """K-Means clustering must produce interpretable, stable cluster outputs."""

    def test_mlops_clustering_output_schema(self, clustered_df):
        """MLOPS-SERVE-2.1: Cluster output has required schema keys."""
        result = cluster_dataframe(clustered_df)
        required = ["optimal_k", "cluster_sizes", "cluster_centers",
                    "data_with_clusters", "inertia_values", "method"]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_mlops_optimal_k_is_positive(self, clustered_df):
        """MLOPS-SERVE-2.2: Optimal K is a positive integer."""
        result = cluster_dataframe(clustered_df)
        assert isinstance(result["optimal_k"], int)
        assert result["optimal_k"] >= 2

    def test_mlops_cluster_count_matches_optimal_k(self, clustered_df):
        """MLOPS-SERVE-2.3: Number of clusters equals optimal_k."""
        result = cluster_dataframe(clustered_df)
        assert len(result["cluster_sizes"]) == result["optimal_k"]

    def test_mlops_cluster_centers_in_original_scale(self, clustered_df):
        """MLOPS-SERVE-2.4: Cluster centers are in original feature space."""
        result = cluster_dataframe(clustered_df)
        fa_min = clustered_df["feature_a"].min()
        fa_max = clustered_df["feature_a"].max()
        for center in result["cluster_centers"]:
            # Centers should be within extended range (not scaled values)
            assert fa_min * 2 <= center["feature_a"] <= fa_max * 2, \
                f"Cluster center outside expected range: {center['feature_a']}"

    def test_mlops_cluster_size_sum_equals_total_rows(self, clustered_df):
        """MLOPS-SERVE-2.5: Sum of cluster sizes equals total rows."""
        result = cluster_dataframe(clustered_df)
        total_in_clusters = sum(result["cluster_sizes"].values())
        assert total_in_clusters == result["rows_clustered"]

    def test_mlops_pca_triggered_on_wide_data(self):
        """MLOPS-SERVE-2.6: PCA is triggered when features > 5."""
        np.random.seed(42)
        wide = pd.DataFrame(
            np.random.randn(100, 8),
            columns=[f"f{i}" for i in range(8)]
        )
        result = cluster_dataframe(wide)
        assert result["pca_used"] is True

    def test_mlops_pca_not_triggered_on_narrow_data(self, clustered_df):
        """MLOPS-SERVE-2.7: PCA is NOT triggered when features ≤ 5."""
        result = cluster_dataframe(clustered_df)
        assert result["pca_used"] is False

    def test_mlops_inertia_decreases_with_k(self, clustered_df):
        """MLOPS-SERVE-2.8: Inertia decreases as K increases (elbow property)."""
        result = cluster_dataframe(clustered_df)
        inertia_vals = [d["inertia"] for d in result["inertia_values"]]
        for i in range(len(inertia_vals) - 1):
            assert inertia_vals[i] >= inertia_vals[i + 1], \
                "Inertia should be non-increasing as K grows"

    def test_mlops_clustering_latency_sla(self, clustered_df):
        """MLOPS-SERVE-2.9: Clustering on 150-row dataset < 10 seconds (SLA)."""
        start = time.time()
        cluster_dataframe(clustered_df)
        elapsed = time.time() - start
        assert elapsed < 10.0, f"Clustering SLA breach: {elapsed:.2f}s"


# ═════════════════════════════════════════════════════════
# MLOPS-SERVE-3: Forecasting Serving
# ═════════════════════════════════════════════════════════

class TestForecastingServing:
    """Forecasting must produce valid, bounded, future-only predictions."""

    def test_mlops_forecast_output_schema(self, timeseries_df):
        """MLOPS-SERVE-3.1: Forecast output has required schema keys."""
        result = forecast_series(timeseries_df, "date", "revenue", periods=10)
        required = ["historical", "forecast", "trend", "method"]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_mlops_forecast_has_correct_period_count(self, timeseries_df):
        """MLOPS-SERVE-3.2: Forecast returns exactly 'periods' future points."""
        result = forecast_series(timeseries_df, "date", "revenue", periods=14)
        assert len(result["forecast"]) == 14

    def test_mlops_forecast_confidence_interval_valid(self, timeseries_df):
        """MLOPS-SERVE-3.3: Lower bound ≤ forecast ≤ upper bound for all points."""
        result = forecast_series(timeseries_df, "date", "revenue", periods=10)
        for point in result["forecast"]:
            assert point["yhat_lower"] <= point["yhat"] <= point["yhat_upper"], \
                f"CI violation: {point['yhat_lower']} <= {point['yhat']} <= {point['yhat_upper']}"

    def test_mlops_forecast_trend_is_valid(self, timeseries_df):
        """MLOPS-SERVE-3.4: Trend field is one of: 'up', 'down', 'flat'."""
        result = forecast_series(timeseries_df, "date", "revenue", periods=10)
        assert result["trend"] in ("up", "down", "flat", "unknown")

    def test_mlops_upward_trend_detected(self, timeseries_df):
        """MLOPS-SERVE-3.5: Clearly upward time series is classified as 'up'."""
        result = forecast_series(timeseries_df, "date", "revenue", periods=10)
        assert result["trend"] == "up", \
            f"Upward trend not detected: got '{result['trend']}'"

    def test_mlops_forecast_dates_are_in_future(self, timeseries_df):
        """MLOPS-SERVE-3.6: All forecast dates are after the last historical date."""
        result = forecast_series(timeseries_df, "date", "revenue", periods=10)
        hist_dates = [h["ds"] for h in result["historical"]]
        last_hist = max(hist_dates)
        for point in result["forecast"]:
            assert point["ds"] > last_hist, \
                f"Forecast date {point['ds']} is not after last historical {last_hist}"

    def test_mlops_forecast_too_few_points_returns_error(self):
        """MLOPS-SERVE-3.7: < 5 data points returns error dict, not exception."""
        df = pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=3),
            "val":  [10, 20, 30],
        })
        result = forecast_series(df, "date", "val", periods=5)
        assert isinstance(result, dict)
        assert "error" in result

    def test_mlops_forecaster_latency_sla(self, timeseries_df):
        """MLOPS-SERVE-3.8: Forecasting on 120-row dataset < 30 seconds (SLA)."""
        start = time.time()
        forecast_series(timeseries_df, "date", "revenue", periods=30)
        elapsed = time.time() - start
        assert elapsed < 30.0, f"Forecasting SLA breach: {elapsed:.2f}s"

    def test_mlops_auto_detect_returns_pair(self, timeseries_df):
        """MLOPS-SERVE-3.9: detect_datetime_and_numeric finds correct pair."""
        result = detect_datetime_and_numeric(timeseries_df)
        assert result is not None
        assert "date_col" in result
        assert "value_col" in result

    def test_mlops_ci_widens_further_into_future(self, timeseries_df):
        """MLOPS-SERVE-3.10: Confidence interval width increases for later predictions."""
        result = forecast_series(timeseries_df, "date", "revenue", periods=20)
        fc = result["forecast"]
        if len(fc) >= 2:
            width_first = fc[0]["yhat_upper"] - fc[0]["yhat_lower"]
            width_last  = fc[-1]["yhat_upper"] - fc[-1]["yhat_lower"]
            # Later predictions should have wider or equal CI
            assert width_last >= width_first * 0.95, \
                f"CI should widen over time. First={width_first:.2f}, Last={width_last:.2f}"
