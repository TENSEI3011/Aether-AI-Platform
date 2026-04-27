"""
============================================================
Forecaster — Simple time-series forecasting service
============================================================
Provides linear regression and moving average predictions
for numeric columns. Used for "predict next N" queries.

Methods:
  - Linear Regression: fits a line and extrapolates
  - Moving Average: uses trailing window average

No external ML libraries needed — uses numpy only.
============================================================
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


def forecast(
    data: List[Dict],
    x_column: str,
    y_column: str,
    periods: int = 5,
    method: str = "linear",
) -> Dict[str, Any]:
    """
    Generate a forecast for the given data.

    Parameters:
        data:     List of row dicts from the query result
        x_column: The x-axis / time column
        y_column: The numeric column to forecast
        periods:  Number of future steps to predict
        method:   "linear" or "moving_average"

    Returns:
        {
            "method": str,
            "historical": [...],   # original data points
            "forecast": [...],     # predicted data points
            "trend": "rising"|"falling"|"stable",
            "confidence": float,   # R² for linear, smoothness for MA
            "summary": str,        # Human-readable summary
        }
    """
    if not data or not y_column:
        return {"error": "No data or column specified for forecasting."}

    df = pd.DataFrame(data)
    if y_column not in df.columns:
        return {"error": f"Column '{y_column}' not found in data."}

    # Extract numeric y values
    y_values = pd.to_numeric(df[y_column], errors="coerce").dropna().values
    if len(y_values) < 3:
        return {"error": "Need at least 3 data points for forecasting."}

    # Extract x labels (could be dates, categories, numbers)
    x_labels = df[x_column].astype(str).tolist() if x_column in df.columns else list(range(len(y_values)))

    # Build historical data points
    historical = [
        {"x": str(x_labels[i]) if i < len(x_labels) else str(i), "y": float(y_values[i])}
        for i in range(len(y_values))
    ]

    if method == "moving_average":
        result = _moving_average_forecast(y_values, x_labels, periods)
    else:
        result = _linear_forecast(y_values, x_labels, periods)

    result["historical"] = historical
    result["method"] = method
    return result


def _linear_forecast(
    y_values: np.ndarray,
    x_labels: List[str],
    periods: int,
) -> Dict[str, Any]:
    """Simple linear regression forecast."""
    n = len(y_values)
    x = np.arange(n, dtype=float)

    # Fit y = mx + b using least squares
    slope, intercept = np.polyfit(x, y_values, 1)

    # R² score (coefficient of determination)
    y_pred = slope * x + intercept
    ss_res = np.sum((y_values - y_pred) ** 2)
    ss_tot = np.sum((y_values - np.mean(y_values)) ** 2)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Generate forecast points
    forecast_points = []
    for i in range(1, periods + 1):
        future_x = n + i - 1
        predicted = slope * future_x + intercept
        forecast_points.append({
            "x": f"Forecast +{i}",
            "y": round(float(predicted), 2),
        })

    # Determine trend
    if slope > 0.01 * np.mean(y_values):
        trend = "rising"
    elif slope < -0.01 * np.mean(y_values):
        trend = "falling"
    else:
        trend = "stable"

    # Summary
    last_val = float(y_values[-1])
    next_val = forecast_points[0]["y"]
    change_pct = ((next_val - last_val) / abs(last_val) * 100) if last_val != 0 else 0

    summary = (
        f"Based on linear regression (R²={r_squared:.2f}), the trend is {trend}. "
        f"The next predicted value is {next_val:.1f} "
        f"({'↑' if change_pct > 0 else '↓'}{abs(change_pct):.1f}% from current {last_val:.1f}). "
        f"Over {periods} periods, values are projected to reach {forecast_points[-1]['y']:.1f}."
    )

    return {
        "forecast": forecast_points,
        "trend": trend,
        "confidence": round(max(0, min(1, r_squared)), 3),
        "slope": round(float(slope), 4),
        "intercept": round(float(intercept), 4),
        "summary": summary,
    }


def _moving_average_forecast(
    y_values: np.ndarray,
    x_labels: List[str],
    periods: int,
    window: int = 3,
) -> Dict[str, Any]:
    """Simple moving average forecast."""
    if window > len(y_values):
        window = len(y_values)

    # Use the last `window` values to compute the forecast
    trailing = y_values[-window:].copy()
    forecast_points = []

    for i in range(1, periods + 1):
        predicted = float(np.mean(trailing))
        forecast_points.append({
            "x": f"Forecast +{i}",
            "y": round(predicted, 2),
        })
        trailing = np.append(trailing[1:], predicted)

    # Trend from historical data
    first_half = np.mean(y_values[:len(y_values)//2])
    second_half = np.mean(y_values[len(y_values)//2:])
    if second_half > first_half * 1.02:
        trend = "rising"
    elif second_half < first_half * 0.98:
        trend = "falling"
    else:
        trend = "stable"

    # Smoothness as a proxy for confidence
    diffs = np.abs(np.diff(y_values))
    mean_diff = np.mean(diffs) if len(diffs) > 0 else 0
    mean_val = np.mean(np.abs(y_values)) if np.mean(np.abs(y_values)) > 0 else 1
    smoothness = max(0, 1.0 - (mean_diff / mean_val))

    last_val = float(y_values[-1])
    next_val = forecast_points[0]["y"]
    summary = (
        f"Based on {window}-period moving average, the trend is {trend}. "
        f"Next predicted value: {next_val:.1f} (current: {last_val:.1f}). "
        f"The forecast smooths to {forecast_points[-1]['y']:.1f} over {periods} periods."
    )

    return {
        "forecast": forecast_points,
        "trend": trend,
        "confidence": round(max(0, min(1, smoothness)), 3),
        "window": window,
        "summary": summary,
    }
