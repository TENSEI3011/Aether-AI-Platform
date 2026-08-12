"""
============================================================
Forecaster — Time-Series Prediction
============================================================
ML Concept: Time-Series Forecasting (Facebook Prophet)
Library:    prophet (install: pip install prophet)

Prophet is an additive regression model that decomposes
a time series into: trend + seasonality + holidays + error.
Uses curve fitting under the hood (Stan/PyStan MCMC).

Falls back to a simple linear trend if Prophet is unavailable.
============================================================
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

# ── Try Prophet ───────────────────────────────────────────
try:
    from prophet import Prophet
    import logging
    logging.getLogger("prophet").setLevel(logging.WARNING)  # suppress verbose logs
    _PROPHET_AVAILABLE = True
except ImportError:
    _PROPHET_AVAILABLE = False

import logging
logger = logging.getLogger(__name__)

if not _PROPHET_AVAILABLE:
    logger.warning("Forecaster: prophet not installed — using linear trend fallback")


# ─────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────

def forecast_series(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    periods: int = 30,
    freq: str = "D",
) -> Dict[str, Any]:
    """
    Generate a time-series forecast for the given date and value columns.

    Parameters:
        df:        Input DataFrame
        date_col:  Name of the datetime column
        value_col: Name of the numeric column to forecast
        periods:   Number of future time steps to predict
        freq:      Frequency: 'D'=daily, 'W'=weekly, 'M'=monthly

    Returns:
        {
            "historical": list of {ds, y} (original data),
            "forecast":   list of {ds, yhat, yhat_lower, yhat_upper},
            "trend": "up" | "down" | "flat",
            "method": "prophet" | "linear_trend",
        }
    """
    # ── Prepare data ──────────────────────────────────────
    try:
        df_copy = df[[date_col, value_col]].dropna().copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors="coerce")
        df_copy = df_copy.dropna()
        df_copy = df_copy.rename(columns={date_col: "ds", value_col: "y"})
        df_copy = df_copy.sort_values("ds").reset_index(drop=True)
    except Exception as e:
        return _error_response(f"Data preparation failed: {e}")

    if len(df_copy) < 5:
        return _error_response("Need at least 5 data points for forecasting.")

    # ── Run forecasting ───────────────────────────────────
    if _PROPHET_AVAILABLE:
        return _prophet_forecast(df_copy, periods, freq)
    return _linear_trend_forecast(df_copy, periods, freq)


def detect_datetime_and_numeric(df: pd.DataFrame) -> Optional[Dict[str, str]]:
    """
    Auto-detect the best (date_col, value_col) pair for forecasting.
    Returns None if no suitable pair is found.
    """
    datetime_cols = []
    numeric_cols = []

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            datetime_cols.append(col)
        elif pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
        else:
            try:
                sample = df[col].dropna().head(20)
                parsed = pd.to_datetime(sample, errors="coerce")
                # Only classify as datetime if >50% of values parse successfully
                if parsed.notna().sum() / max(len(sample), 1) > 0.5:
                    datetime_cols.append(col)
            except Exception:
                pass

    if datetime_cols and numeric_cols:
        return {"date_col": datetime_cols[0], "value_col": numeric_cols[0]}
    return None


# ─────────────────────────────────────────────────────────
# Forecasting implementations
# ─────────────────────────────────────────────────────────

def _prophet_forecast(
    df: pd.DataFrame,
    periods: int,
    freq: str,
) -> Dict[str, Any]:
    """Use Facebook Prophet for forecasting."""
    try:
        model = Prophet(
            yearly_seasonality="auto",
            weekly_seasonality="auto",
            daily_seasonality=False,
            interval_width=0.8,  # 80% confidence interval
        )
        model.fit(df)

        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast = model.predict(future)

        # ── Historical portion ────────────────────────────
        historical = [
            {"ds": str(row["ds"].date()), "y": round(float(row["y"]), 4)}
            for _, row in df.iterrows()
        ]

        # ── Forecast (future only) ────────────────────────
        future_only = forecast[forecast["ds"] > df["ds"].max()]
        forecast_data = [
            {
                "ds": str(row["ds"].date()),
                "yhat": round(float(row["yhat"]), 4),
                "yhat_lower": round(float(row["yhat_lower"]), 4),
                "yhat_upper": round(float(row["yhat_upper"]), 4),
            }
            for _, row in future_only.iterrows()
        ]

        # ── Trend direction ───────────────────────────────
        trend_vals = forecast["trend"].values
        trend = _classify_trend(trend_vals)

        return {
            "historical": historical,
            "forecast": forecast_data,
            "trend": trend,
            "method": "prophet",
            "periods": periods,
            "frequency": freq,
        }

    except Exception as e:
        logger.warning("Forecaster: Prophet failed: %s — using linear fallback", e)
        return _linear_trend_forecast(df, periods, freq)


def _linear_trend_forecast(
    df: pd.DataFrame,
    periods: int,
    freq: str,
) -> Dict[str, Any]:
    """Simple linear regression trend fallback.

    FIX: Confidence interval is now based on the actual residual
    standard deviation from the linear fit (±1.96σ = 95% CI)
    instead of the hardcoded ±10% band which is inaccurate for
    volatile datasets.
    """
    try:
        x = np.arange(len(df), dtype=float)
        y = df["y"].values.astype(float)
        coeffs = np.polyfit(x, y, 1)  # slope + intercept
        slope, intercept = coeffs

        # ── Compute residual std for real confidence interval ──
        y_pred = slope * x + intercept
        residuals = y - y_pred
        residual_std = float(np.std(residuals))
        z_95 = 1.96  # 95% confidence interval
        margin = z_95 * residual_std

        historical = [
            {"ds": str(row["ds"].date()), "y": round(float(row["y"]), 4)}
            for _, row in df.iterrows()
        ]

        last_ds = df["ds"].max()
        freq_map = {"D": "1D", "W": "7D", "M": "30D"}
        delta = pd.Timedelta(freq_map.get(freq, "1D"))

        forecast_data = []
        for i in range(1, periods + 1):
            future_x = float(len(df) + i - 1)
            yhat = float(slope * future_x + intercept)
            # Widen interval slightly as we go further into the future
            future_margin = margin * (1 + i / (periods * 2))
            forecast_data.append({
                "ds":         str((last_ds + delta * i).date()),
                "yhat":       round(yhat, 4),
                "yhat_lower": round(yhat - future_margin, 4),
                "yhat_upper": round(yhat + future_margin, 4),
            })

        trend = "up" if slope > 0 else ("down" if slope < 0 else "flat")

        return {
            "historical": historical,
            "forecast":   forecast_data,
            "trend":      trend,
            "method":     "linear_trend",
            "periods":    periods,
            "frequency":  freq,
        }
    except Exception as e:
        return _error_response(f"Linear trend failed: {e}")


def _classify_trend(values: np.ndarray) -> str:
    """Classify overall trend direction from trend values."""
    if len(values) < 2:
        return "flat"
    delta = values[-1] - values[0]
    pct_change = delta / (abs(values[0]) + 1e-9)
    if pct_change > 0.05:
        return "up"
    elif pct_change < -0.05:
        return "down"
    return "flat"


def _error_response(msg: str) -> Dict[str, Any]:
    return {
        "historical": [],
        "forecast": [],
        "trend": "unknown",
        "method": "none",
        "error": msg,
    }
