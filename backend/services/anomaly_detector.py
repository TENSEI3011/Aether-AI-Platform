"""
============================================================
Anomaly Detector — Identifies outliers in numeric columns
============================================================
ML Concept: Unsupervised Anomaly Detection (Isolation Forest)
Library:    scikit-learn

Isolation Forest works by randomly partitioning data using
decision trees. Anomalous points are isolated in fewer splits
(shorter path length) than normal points.

Falls back to Z-score method if scikit-learn is unavailable.
============================================================
"""

from __future__ import annotations
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ── Try scikit-learn ──────────────────────────────────────
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    logger.warning("AnomalyDetector: scikit-learn not installed — using Z-score fallback")


# ─────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────

def detect_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.05,
    numeric_cols: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Detect anomalies in numeric columns of the DataFrame.

    Parameters:
        df:            Input DataFrame
        contamination: Expected proportion of anomalies (0.01–0.5)
        numeric_cols:  Specific columns to check (None = all numeric)

    Returns:
        {
            "anomaly_count": int,
            "anomaly_indices": list of int,
            "anomaly_rows": list of dicts (the anomalous rows),
            "column_stats": dict per column with threshold info,
            "method": "isolation_forest" or "zscore",
        }
    """
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not numeric_cols:
        return {
            "anomaly_count": 0,
            "anomaly_indices": [],
            "anomaly_rows": [],
            "column_stats": {},
            "method": "none",
            "message": "No numeric columns found for anomaly detection.",
        }

    # Only keep numeric cols with no all-NaN
    valid_cols = [c for c in numeric_cols if not df[c].isna().all()]
    if not valid_cols:
        return {
            "anomaly_count": 0,
            "anomaly_indices": [],
            "anomaly_rows": [],
            "column_stats": {},
            "method": "none",
            "message": "All numeric columns are empty.",
        }

    # ── Run detection ─────────────────────────────────────
    df_clean = df[valid_cols].dropna()
    original_indices = df_clean.index.tolist()

    if _SKLEARN_AVAILABLE:
        labels, method = _isolation_forest(df_clean, contamination)
    else:
        labels, method = _zscore_method(df_clean)

    anomaly_mask = labels == -1
    anomaly_idx = [original_indices[i] for i, flag in enumerate(anomaly_mask) if flag]

    # ── Column-level statistics ───────────────────────────
    column_stats = {}
    for col in valid_cols:
        series = df_clean[col]
        column_stats[col] = {
            "mean": round(float(series.mean()), 4),
            "std":  round(float(series.std()), 4),
            "min":  round(float(series.min()), 4),
            "max":  round(float(series.max()), 4),
        }

    # ── Anomalous rows (limit to 50 for response size) ───
    anomaly_rows = df.loc[anomaly_idx[:50]].to_dict(orient="records")

    return {
        "anomaly_count": int(anomaly_mask.sum()),
        "anomaly_indices": anomaly_idx[:50],
        "anomaly_rows": anomaly_rows,
        "column_stats": column_stats,
        "method": method,
        "total_rows_checked": len(df_clean),
        "contamination_rate": round(float(anomaly_mask.sum()) / max(len(df_clean), 1), 4),
    }


def add_anomaly_column(
    df: pd.DataFrame,
    contamination: float = 0.05,
    numeric_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Return a copy of df with an 'is_anomaly' boolean column added.
    Useful for the query engine to filter anomalies.
    """
    result = detect_anomalies(df, contamination, numeric_cols)
    df_copy = df.copy()
    df_copy["is_anomaly"] = False
    if result["anomaly_indices"]:
        df_copy.loc[result["anomaly_indices"], "is_anomaly"] = True
    return df_copy


# ─────────────────────────────────────────────────────────
# Detection methods
# ─────────────────────────────────────────────────────────

def _isolation_forest(
    df: pd.DataFrame,
    contamination: float,
) -> tuple[np.ndarray, str]:
    """
    Isolation Forest anomaly detection.
    Returns (labels_array, method_name).
    Labels: -1 = anomaly, 1 = normal.
    """
    try:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df.fillna(df.mean()))

        clf = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        labels = clf.fit_predict(X_scaled)
        return labels, "isolation_forest"
    except Exception as e:
        logger.warning("AnomalyDetector: IsolationForest failed: %s — using Z-score", e)
        return _zscore_method(df)


def _zscore_method(df: pd.DataFrame) -> tuple[np.ndarray, str]:
    """
    Z-score fallback: flag rows where any column > 3 std from mean.
    """
    z_scores = np.abs((df - df.mean()) / (df.std() + 1e-9))
    is_anomaly = (z_scores > 3).any(axis=1)
    labels = np.where(is_anomaly, -1, 1)
    return labels, "zscore"
