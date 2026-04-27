"""
============================================================
Anomaly Detector — Lightweight outlier detection
============================================================
Detects anomalies in numeric query results using:
  1. Z-score method  (|z| > 3)
  2. IQR method      (value outside Q1-1.5*IQR .. Q3+1.5*IQR)

Returns flagged data points with messages for visualization.
============================================================
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


def detect_anomalies(
    data: List[Dict],
    columns: List[str],
    z_threshold: float = 3.0,
    iqr_multiplier: float = 1.5,
) -> Dict[str, Any]:
    """
    Scan numeric columns in the query result for outliers.

    Parameters:
        data:           list of row dicts (from query executor)
        columns:        list of column names
        z_threshold:    Z-score cutoff (default 3.0 → flag |z| > 3)
        iqr_multiplier: IQR fence multiplier (default 1.5 → Q1-1.5*IQR .. Q3+1.5*IQR)

    Returns:
        {
            "anomalies": [ {column, row_index, value, method, message} ],
            "anomaly_count": int,
            "insights": [ "Unusual spike detected..." ],
            "anomaly_indices": { column: [row_indices] },
            "thresholds": { "z_threshold": float, "iqr_multiplier": float }
        }
    """
    if not data or not columns:
        return {
            "anomalies": [],
            "anomaly_count": 0,
            "insights": [],
            "anomaly_indices": {},
            "thresholds": {"z_threshold": z_threshold, "iqr_multiplier": iqr_multiplier},
        }

    df = pd.DataFrame(data)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    all_anomalies = []
    anomaly_indices = {}
    insights = []

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 5:
            # Too few data points for meaningful detection
            continue

        col_anomalies = set()

        # ── Z-Score Method ────────────────────────────────
        mean = series.mean()
        std = series.std()
        if std > 0:
            z_scores = (series - mean) / std
            z_outliers = z_scores[z_scores.abs() > z_threshold]
            for idx in z_outliers.index:
                value = float(df.loc[idx, col])
                col_anomalies.add(int(idx))
                all_anomalies.append({
                    "column": col,
                    "row_index": int(idx),
                    "value": value,
                    "method": "zscore",
                    "z_score": round(float(z_scores[idx]), 2),
                    "message": f"Unusual value {value} in '{col}' (z-score: {round(float(z_scores[idx]), 2)})",
                })

        # ── IQR Method ────────────────────────────────────
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            lower = q1 - iqr_multiplier * iqr
            upper = q3 + iqr_multiplier * iqr
            iqr_outliers = series[(series < lower) | (series > upper)]
            for idx in iqr_outliers.index:
                if int(idx) not in col_anomalies:  # avoid duplicates
                    value = float(df.loc[idx, col])
                    col_anomalies.add(int(idx))
                    direction = "spike" if value > upper else "drop"
                    all_anomalies.append({
                        "column": col,
                        "row_index": int(idx),
                        "value": value,
                        "method": "iqr",
                        "message": f"Unusual {direction} in '{col}': {value} (outside IQR range [{round(lower, 2)}, {round(upper, 2)}])",
                    })

        if col_anomalies:
            anomaly_indices[col] = sorted(col_anomalies)

            # Generate insight message
            count = len(col_anomalies)
            # Try to identify location context
            if len(df.columns) > 1:
                # Find a categorical/label column for context
                label_cols = [c for c in df.columns if c != col and not pd.api.types.is_numeric_dtype(df[c])]
                if label_cols:
                    label_col = label_cols[0]
                    for idx in list(col_anomalies)[:3]:  # Max 3 insights per column
                        label = str(df.loc[idx, label_col])
                        value = float(df.loc[idx, col])
                        insights.append(f"Unusual {'spike' if value > mean else 'drop'} detected in '{col}' at {label_col}='{label}'")
                else:
                    insights.append(f"{count} anomal{'y' if count == 1 else 'ies'} detected in '{col}'")
            else:
                insights.append(f"{count} anomal{'y' if count == 1 else 'ies'} detected in '{col}'")

    return {
        "anomalies": all_anomalies,
        "anomaly_count": len(all_anomalies),
        "insights": insights[:10],
        "anomaly_indices": anomaly_indices,
        "thresholds": {"z_threshold": z_threshold, "iqr_multiplier": iqr_multiplier},
    }
