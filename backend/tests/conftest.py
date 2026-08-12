"""
============================================================
conftest.py — Shared pytest fixtures for all test modules
============================================================
AI DLS Phase: Data Preparation & Validation
Provides reusable DataFrames covering:
  - Clean numeric/categorical/datetime data
  - Dirty data (nulls, duplicates, mixed types)
  - Injected anomalies
  - Time-series data for forecasting
============================================================
"""

import pytest
import pandas as pd
import numpy as np


# ── 1. Clean mixed dataset ─────────────────────────────────
@pytest.fixture
def clean_df():
    """Standard clean DataFrame with numeric + categorical + datetime cols."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        "id":         range(1, n + 1),                                        # ID col
        "age":        np.random.randint(18, 65, n),                           # numeric
        "salary":     np.random.randint(30_000, 120_000, n).astype(float),   # numeric
        "department": np.random.choice(["HR", "Eng", "Sales", "Finance"], n), # categorical
        "is_remote":  np.random.choice([0, 1], n),                            # binary flag
        "join_date":  pd.date_range("2020-01-01", periods=n, freq="3D"),      # datetime
    })


# ── 2. Dirty dataset ──────────────────────────────────────
@pytest.fixture
def dirty_df():
    """DataFrame with nulls, duplicates, and mixed types."""
    base = pd.DataFrame({
        "name":   ["Alice", "Bob", None, "Dave", "Alice"],
        "score":  [95, None, 78, 82, 95],
        "grade":  ["A", "B", "C", None, "A"],
        "amount": ["100", "200", "abc", "400", "100"],   # mixed type
    })
    return base


# ── 3. Pure numeric dataset (for clustering) ─────────────
@pytest.fixture
def numeric_df():
    """Well-separated clusters for K-Means testing."""
    np.random.seed(0)
    cluster1 = np.random.randn(40, 3) + [0, 0, 0]
    cluster2 = np.random.randn(40, 3) + [10, 10, 10]
    cluster3 = np.random.randn(20, 3) + [5, -5, 5]
    data = np.vstack([cluster1, cluster2, cluster3])
    return pd.DataFrame(data, columns=["x", "y", "z"])


# ── 4. Dataset with injected anomalies ────────────────────
@pytest.fixture
def anomaly_df():
    """Normal data with 5 clear outliers injected."""
    np.random.seed(7)
    normal = pd.DataFrame({
        "value_a": np.random.normal(50, 5, 95),
        "value_b": np.random.normal(100, 10, 95),
    })
    outliers = pd.DataFrame({
        "value_a": [500, -500, 450, -450, 480],
        "value_b": [1000, -1000, 900, -900, 950],
    })
    return pd.concat([normal, outliers], ignore_index=True)


# ── 5. Time-series dataset ────────────────────────────────
@pytest.fixture
def timeseries_df():
    """Upward-trending time series for forecaster testing."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=90, freq="D")
    trend = np.linspace(100, 200, 90)
    noise = np.random.normal(0, 5, 90)
    return pd.DataFrame({
        "date":  dates,
        "sales": (trend + noise).round(2),
    })


# ── 6. Wide dataset (for PCA clustering test) ────────────
@pytest.fixture
def wide_df():
    """10 correlated numeric columns — triggers PCA path in clustering."""
    np.random.seed(42)
    n = 150
    base = np.random.randn(n, 2)     # 2 underlying factors
    cols = {}
    for i in range(10):
        cols[f"feat_{i}"] = base[:, i % 2] * (i + 1) + np.random.randn(n) * 0.1
    return pd.DataFrame(cols)
