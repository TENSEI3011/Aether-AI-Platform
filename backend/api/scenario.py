"""
============================================================
Scenario API — What-If / Scenario Analysis
============================================================
Endpoints:
  POST /api/scenario/what-if → Apply mutations, compare results
============================================================
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from database.models import User
from services.data_validator import load_dataframe
from services.forecaster import forecast
from services.insight_generator import generate_insights
from api.datasets import _datasets as datasets_store

import pandas as pd

router = APIRouter()


class Mutation(BaseModel):
    column: str
    operation: str    # "increase_pct", "decrease_pct", "set_value", "multiply"
    value: float


class WhatIfRequest(BaseModel):
    dataset_id: str
    mutations: List[Mutation]
    forecast_x: Optional[str] = None
    forecast_y: Optional[str] = None
    forecast_periods: int = 5


@router.post("/what-if")
def what_if_analysis(
    req: WhatIfRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Apply user-specified mutations to a dataset copy and compare
    original vs mutated insights and forecasts.
    """
    if req.dataset_id not in datasets_store:
        raise HTTPException(status_code=404, detail="Dataset not found")
    ds = datasets_store[req.dataset_id]
    if ds.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    # Load original DataFrame
    df_original = load_dataframe(ds["filepath"])
    df_mutated = df_original.copy()

    # Apply mutations
    applied_mutations = []
    for m in req.mutations:
        if m.column not in df_mutated.columns:
            continue
        if not pd.api.types.is_numeric_dtype(df_mutated[m.column]):
            continue

        before_mean = float(df_mutated[m.column].mean())

        if m.operation == "increase_pct":
            df_mutated[m.column] = df_mutated[m.column] * (1 + m.value / 100)
        elif m.operation == "decrease_pct":
            df_mutated[m.column] = df_mutated[m.column] * (1 - m.value / 100)
        elif m.operation == "set_value":
            df_mutated[m.column] = m.value
        elif m.operation == "multiply":
            df_mutated[m.column] = df_mutated[m.column] * m.value

        after_mean = float(df_mutated[m.column].mean())
        applied_mutations.append({
            "column": m.column,
            "operation": m.operation,
            "value": m.value,
            "before_mean": round(before_mean, 2),
            "after_mean": round(after_mean, 2),
        })

    # Generate insights for both
    orig_data = df_original.to_dict("records")
    mut_data = df_mutated.to_dict("records")
    orig_columns = list(df_original.columns)
    mut_columns = list(df_mutated.columns)

    original_insights = generate_insights(orig_data, orig_columns)
    mutated_insights = generate_insights(mut_data, mut_columns)

    result = {
        "success": True,
        "mutations_applied": applied_mutations,
        "original": {
            "insights": original_insights,
            "row_count": len(df_original),
            "preview": orig_data[:10],
        },
        "mutated": {
            "insights": mutated_insights,
            "row_count": len(df_mutated),
            "preview": mut_data[:10],
        },
    }

    # Optional: run forecast comparison
    if req.forecast_x and req.forecast_y:
        if req.forecast_x in orig_columns and req.forecast_y in orig_columns:
            orig_forecast = forecast(
                data=orig_data,
                x_column=req.forecast_x,
                y_column=req.forecast_y,
                periods=req.forecast_periods,
                method="linear",
            )
            mut_forecast = forecast(
                data=mut_data,
                x_column=req.forecast_x,
                y_column=req.forecast_y,
                periods=req.forecast_periods,
                method="linear",
            )
            result["original"]["forecast"] = orig_forecast
            result["mutated"]["forecast"] = mut_forecast

    return result
