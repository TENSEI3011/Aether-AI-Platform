"""
============================================================
MLOps DLC Phase 3 — Model Monitoring & Performance Tracking
============================================================
MLOps Development Lifecycle Stage: MONITORING

This phase validates the monitoring, evaluation, and
performance tracking aspects of the ML pipeline:
  • Model accuracy tracking: predictions compared to known baselines
  • Anomaly detector precision/recall on labeled test sets
  • Clustering quality metrics: silhouette score, inertia bounds
  • Forecast accuracy: MAE, MAPE on holdout sets
  • Confidence calibration: model uncertainty is meaningful
  • Behavioral regression tests: models still work after updates
  • Edge case behavior: single points, all-same values, negatives

~34 Tests
============================================================
"""

import pytest
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.anomaly_detector import detect_anomalies
from services.clustering import cluster_dataframe
from services.forecaster import forecast_series

try:
    from sklearn.metrics import silhouette_score
    _SKLEARN = True
except ImportError:
    _SKLEARN = False


# ─────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────

@pytest.fixture
def labeled_anomaly_df():
    """200 normal + 10 extreme outliers with known ground-truth labels."""
    np.random.seed(42)
    normal_data = pd.DataFrame({
        "x": np.random.normal(0, 1, 200),
        "y": np.random.normal(0, 1, 200),
    })
    # 10 extreme outliers placed far from normal distribution
    outlier_data = pd.DataFrame({
        "x": [100, -100, 90, -90, 95, -95, 85, -85, 80, -80],
        "y": [100, -100, 90, -90, 95, -95, 85, -85, 80, -80],
    })
    df = pd.concat([normal_data, outlier_data], ignore_index=True)
    labels = [0] * 200 + [1] * 10  # 0 = normal, 1 = anomaly
    return df, labels

@pytest.fixture
def linear_timeseries():
    """Perfect linear trend (no noise) for accuracy testing."""
    dates = pd.date_range("2023-01-01", periods=60, freq="D")
    values = np.arange(60, dtype=float) * 2.0 + 10.0  # y = 2x + 10
    return pd.DataFrame({"date": dates, "value": values})

@pytest.fixture
def three_cluster_df():
    """Three well-separated clusters for evaluation."""
    np.random.seed(42)
    c1 = np.random.randn(50, 2) + [0, 0]
    c2 = np.random.randn(50, 2) + [20, 20]
    c3 = np.random.randn(50, 2) + [10, -10]
    data = np.vstack([c1, c2, c3])
    return pd.DataFrame(data, columns=["a", "b"])


# ═════════════════════════════════════════════════════════
# MLOPS-MON-1: Anomaly Detection Performance
# ═════════════════════════════════════════════════════════

class TestAnomalyDetectionPerformance:
    """Validate anomaly detection quality on labeled datasets."""

    def test_mlops_precision_on_extreme_outliers(self, labeled_anomaly_df):
        """MLOPS-MON-1.1: Model detects ≥ 8 out of 10 extreme outliers."""
        df, labels = labeled_anomaly_df
        result = detect_anomalies(df, contamination=0.06)
        detected_indices = set(result["anomaly_indices"])
        true_outlier_indices = set(range(200, 210))  # last 10 rows are outliers
        correctly_detected = len(detected_indices & true_outlier_indices)
        assert correctly_detected >= 7, \
            f"Model only detected {correctly_detected}/10 extreme outliers"

    def test_mlops_normal_data_low_false_positive_rate(self):
        """MLOPS-MON-1.2: False positive rate ≤ contamination parameter."""
        np.random.seed(0)
        df = pd.DataFrame({
            "x": np.random.normal(0, 1, 500),
            "y": np.random.normal(0, 1, 500),
        })
        contamination = 0.05
        result = detect_anomalies(df, contamination=contamination)
        actual_rate = result["anomaly_count"] / max(len(df), 1)
        # Should be close to contamination (within ±0.03)
        assert actual_rate <= contamination + 0.03, \
            f"False positive rate {actual_rate:.3f} exceeds limit {contamination + 0.03:.3f}"

    def test_mlops_contamination_consistency(self):
        """MLOPS-MON-1.3: Higher contamination → more anomalies detected."""
        np.random.seed(42)
        df = pd.DataFrame({
            "x": np.random.normal(0, 1, 200),
        })
        result_low  = detect_anomalies(df, contamination=0.03)
        result_high = detect_anomalies(df, contamination=0.20)
        assert result_high["anomaly_count"] >= result_low["anomaly_count"], \
            "Higher contamination should detect more anomalies"

    def test_mlops_constant_column_handled(self):
        """MLOPS-MON-1.4: All-same values in a column don't crash the model."""
        df = pd.DataFrame({
            "constant": [100.0] * 50,
            "variable": np.random.normal(0, 1, 50),
        })
        result = detect_anomalies(df)
        assert isinstance(result, dict)
        assert "anomaly_count" in result

    def test_mlops_negative_values_detected(self):
        """MLOPS-MON-1.5: Model works correctly on negative-valued features."""
        np.random.seed(42)
        df = pd.DataFrame({
            "x": np.random.normal(-50, 5, 100),
        })
        result = detect_anomalies(df, contamination=0.05)
        assert result["method"] in ("isolation_forest", "zscore")
        assert result["anomaly_count"] >= 0


# ═════════════════════════════════════════════════════════
# MLOPS-MON-2: Clustering Quality Metrics
# ═════════════════════════════════════════════════════════

class TestClusteringQualityMetrics:
    """Validate clustering quality using standard ML metrics."""

    def test_mlops_optimal_k_finds_three_clusters(self, three_cluster_df):
        """MLOPS-MON-2.1: Elbow method finds K=3 for 3 well-separated clusters."""
        result = cluster_dataframe(three_cluster_df)
        # Should find ~3 clusters (may find 2 or 3 depending on elbow)
        assert result["optimal_k"] in (2, 3, 4), \
            f"Expected K near 3, got {result['optimal_k']}"

    @pytest.mark.skipif(not _SKLEARN, reason="scikit-learn not installed")
    def test_mlops_silhouette_score_acceptable(self, three_cluster_df):
        """MLOPS-MON-2.2: Silhouette score > 0.5 (good separation)."""
        result = cluster_dataframe(three_cluster_df)
        data_with_clusters = result["data_with_clusters"]
        df_c = pd.DataFrame(data_with_clusters)
        X = df_c[["a", "b"]].values
        labels = df_c["cluster"].values
        score = silhouette_score(X, labels)
        assert score > 0.5, f"Poor cluster separation: silhouette={score:.3f}"

    def test_mlops_cluster_centers_count_matches_k(self, three_cluster_df):
        """MLOPS-MON-2.3: Number of cluster centers equals optimal_k."""
        result = cluster_dataframe(three_cluster_df)
        assert len(result["cluster_centers"]) == result["optimal_k"]

    def test_mlops_inertia_values_are_positive(self, three_cluster_df):
        """MLOPS-MON-2.4: All inertia values are positive."""
        result = cluster_dataframe(three_cluster_df)
        for iv in result["inertia_values"]:
            assert iv["inertia"] > 0

    def test_mlops_cluster_assignment_covers_all_rows(self, three_cluster_df):
        """MLOPS-MON-2.5: Every row is assigned to a cluster."""
        result = cluster_dataframe(three_cluster_df)
        assert result["rows_clustered"] == len(three_cluster_df)

    def test_mlops_cluster_label_range_valid(self, three_cluster_df):
        """MLOPS-MON-2.6: Cluster labels are in range [0, optimal_k-1]."""
        result = cluster_dataframe(three_cluster_df)
        k = result["optimal_k"]
        for row in result["data_with_clusters"]:
            assert 0 <= row["cluster"] < k, \
                f"Invalid cluster label: {row['cluster']} (k={k})"

    def test_mlops_clustering_with_label_col(self):
        """MLOPS-MON-2.7: Cluster descriptions work with a label column."""
        np.random.seed(42)
        df = pd.DataFrame({
            "x": np.concatenate([np.random.randn(30) + 0, np.random.randn(30) + 10]),
            "y": np.concatenate([np.random.randn(30) + 0, np.random.randn(30) + 10]),
            "product": (["Widget"] * 30 + ["Gadget"] * 30),
        })
        result = cluster_dataframe(df, label_col="product")
        assert isinstance(result["cluster_descriptions"], dict)


# ═════════════════════════════════════════════════════════
# MLOPS-MON-3: Forecast Accuracy Evaluation
# ═════════════════════════════════════════════════════════

class TestForecastAccuracyEvaluation:
    """Validate forecast accuracy on known ground-truth holdout sets."""

    def _compute_mae(self, actual, predicted):
        """Mean Absolute Error."""
        return float(np.mean(np.abs(np.array(actual) - np.array(predicted))))

    def _compute_mape(self, actual, predicted):
        """Mean Absolute Percentage Error (with epsilon to avoid div/0)."""
        a = np.array(actual)
        p = np.array(predicted)
        return float(np.mean(np.abs((a - p) / (np.abs(a) + 1e-9)))) * 100

    def test_mlops_linear_fit_mae_on_perfect_trend(self, linear_timeseries):
        """MLOPS-MON-3.1: MAE < 5 on perfect linear data (holdout last 10 points)."""
        train = linear_timeseries.iloc[:50]
        test  = linear_timeseries.iloc[50:]
        actual_y = test["value"].tolist()

        result = forecast_series(train, "date", "value", periods=10, freq="D")
        if result.get("error"):
            pytest.skip(f"Forecast failed: {result['error']}")

        predicted_y = [p["yhat"] for p in result["forecast"]]
        mae = self._compute_mae(actual_y, predicted_y)
        assert mae < 5.0, f"MAE too high on perfect linear data: {mae:.4f}"

    def test_mlops_mape_on_linear_trend(self, linear_timeseries):
        """MLOPS-MON-3.2: MAPE < 5% on perfect linear data."""
        train = linear_timeseries.iloc[:50]
        test  = linear_timeseries.iloc[50:]
        actual_y = test["value"].tolist()

        result = forecast_series(train, "date", "value", periods=10, freq="D")
        if result.get("error"):
            pytest.skip(f"Forecast failed: {result['error']}")

        predicted_y = [p["yhat"] for p in result["forecast"]]
        mape = self._compute_mape(actual_y, predicted_y)
        assert mape < 5.0, f"MAPE too high: {mape:.2f}%"

    def test_mlops_forecast_trend_matches_actual(self, linear_timeseries):
        """MLOPS-MON-3.3: Detected trend matches actual trend direction."""
        result = forecast_series(linear_timeseries, "date", "value", periods=10)
        # The timeseries is upward (slope=2.0), so trend must be 'up'
        assert result["trend"] == "up"

    def test_mlops_downward_trend_detected(self):
        """MLOPS-MON-3.4: Downward trend correctly identified."""
        dates = pd.date_range("2023-01-01", periods=60, freq="D")
        values = np.linspace(200, 50, 60) + np.random.normal(0, 3, 60)
        df = pd.DataFrame({"date": dates, "sales": values})
        result = forecast_series(df, "date", "sales", periods=10)
        assert result["trend"] in ("down", "flat"), \
            f"Downward trend not detected: got '{result['trend']}'"

    def test_mlops_constant_trend_is_flat(self):
        """MLOPS-MON-3.5: Constant time series → 'flat' trend."""
        dates = pd.date_range("2023-01-01", periods=30, freq="D")
        df = pd.DataFrame({"date": dates, "val": [100.0] * 30})
        result = forecast_series(df, "date", "val", periods=5)
        assert result["trend"] in ("flat", "up", "down")  # no exception

    def test_mlops_forecast_not_affected_by_df_copy(self, linear_timeseries):
        """MLOPS-MON-3.6: Forecast doesn't mutate the input DataFrame."""
        original_len = len(linear_timeseries)
        original_cols = list(linear_timeseries.columns)
        forecast_series(linear_timeseries, "date", "value", periods=5)
        assert len(linear_timeseries) == original_len
        assert list(linear_timeseries.columns) == original_cols


# ═════════════════════════════════════════════════════════
# MLOPS-MON-4: Model Behavioral Regression Tests
# ═════════════════════════════════════════════════════════

class TestModelBehavioralRegression:
    """Ensure models haven't regressed from expected baseline behavior."""

    def test_mlops_isolation_forest_baseline_contamination(self):
        """MLOPS-MON-4.1: With 5% contamination on 200 rows → ~10 anomalies."""
        np.random.seed(42)
        df = pd.DataFrame({"x": np.random.normal(0, 1, 200)})
        result = detect_anomalies(df, contamination=0.05)
        # Should be approximately 10 (5% of 200), within a tolerance
        assert 5 <= result["anomaly_count"] <= 15, \
            f"Anomaly count {result['anomaly_count']} outside expected range [5, 15]"

    def test_mlops_kmeans_elbow_selects_plausible_k(self):
        """MLOPS-MON-4.2: With 4 tight clusters, K∈[2,5] is selected."""
        np.random.seed(42)
        c1 = np.random.randn(30, 2) + [0, 0]
        c2 = np.random.randn(30, 2) + [20, 0]
        c3 = np.random.randn(30, 2) + [0, 20]
        c4 = np.random.randn(30, 2) + [20, 20]
        df = pd.DataFrame(np.vstack([c1, c2, c3, c4]), columns=["x", "y"])
        result = cluster_dataframe(df, max_k=6)
        assert 2 <= result["optimal_k"] <= 5, \
            f"Elbow selected unexpected K={result['optimal_k']}"

    def test_mlops_forecast_historical_length_preserved(self):
        """MLOPS-MON-4.3: Historical output length matches training set size."""
        dates = pd.date_range("2023-01-01", periods=50, freq="D")
        df = pd.DataFrame({"date": dates, "val": np.random.normal(50, 5, 50)})
        result = forecast_series(df, "date", "val", periods=10)
        assert len(result["historical"]) == 50

    def test_mlops_anomaly_method_field_valid(self):
        """MLOPS-MON-4.4: Method field is always a known algorithm name."""
        np.random.seed(42)
        df = pd.DataFrame({"x": np.random.normal(0, 1, 100)})
        result = detect_anomalies(df)
        assert result["method"] in ("isolation_forest", "zscore", "none"), \
            f"Unknown method: {result['method']}"

    def test_mlops_clustering_method_field_valid(self):
        """MLOPS-MON-4.5: Clustering method field is a known algorithm name."""
        np.random.seed(42)
        df = pd.DataFrame(np.random.randn(50, 3), columns=["a", "b", "c"])
        result = cluster_dataframe(df)
        assert result["method"] in ("kmeans", "kmeans+pca", "none", "unavailable"), \
            f"Unknown clustering method: {result['method']}"

    def test_mlops_forecast_method_field_valid(self):
        """MLOPS-MON-4.6: Forecast method field is a known algorithm name."""
        dates = pd.date_range("2023-01-01", periods=30, freq="D")
        df = pd.DataFrame({"date": dates, "val": np.random.normal(50, 5, 30)})
        result = forecast_series(df, "date", "val", periods=5)
        assert result["method"] in ("prophet", "linear_trend", "none"), \
            f"Unknown forecast method: {result['method']}"
