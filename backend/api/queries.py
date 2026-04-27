"""
============================================================
Queries API — Natural language query pipeline
============================================================
Endpoints:
  POST /api/queries/ask      → Process a natural language query
  GET  /api/queries/history   → Get query history

Pipeline:
  NL Query → LLM (generate code) → Validate → Execute →
  Select Viz → Generate Insights → Log → Return

IMPORTANT: Each request is processed independently. No global
state or caching. Every call creates fresh local variables.
============================================================
"""

import json
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from database.session import get_db
from database.models import User
from services.data_validator import load_dataframe, create_data_profile
from services.query_validator import validate_query
from services.query_executor import execute_query
from services.viz_selector import select_visualization
from services.insight_generator import generate_insights
from services.anomaly_detector import detect_anomalies
from services.query_logger import log_query, get_user_history
from services.context_manager import add_to_context, build_context_string
from services.schema_extractor import extract_schema, generate_schema_summary
from services.forecaster import forecast
from llm.llm_engine import llm_engine
from api.datasets import get_dataset_store

router = APIRouter()


# ── Dataset ownership helper ──────────────────────────────
def _get_user_dataset(dataset_id: str, user_id: int) -> dict:
    """
    Retrieve a dataset from the store, verifying it belongs to the user.
    Raises 404 or 403 as appropriate.
    """
    datasets = get_dataset_store()
    if dataset_id not in datasets:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found. Please upload a dataset first.",
        )
    dataset = datasets[dataset_id]
    if dataset.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorised to access this dataset",
        )
    return dataset


# ── Request/Response schemas ──────────────────────────────

class QueryRequest(BaseModel):
    dataset_id:      str
    query:           str
    graph_type:      Optional[str]   = "auto"
    session_id:      Optional[str]   = None
    z_threshold:     Optional[float] = 3.0
    iqr_multiplier:  Optional[float] = 1.5


class CleanRequest(BaseModel):
    dataset_id: str
    instruction: str  # e.g. "remove duplicates", "fill missing values with 0"
    persist: Optional[bool] = True  # whether to save changes to disk


class ForecastRequest(BaseModel):
    dataset_id: str
    x_column: str
    y_column: str
    periods: Optional[int] = 5
    method: Optional[str] = "linear"  # "linear" or "moving_average"


class QueryHistoryItem(BaseModel):
    id: int
    natural_query: str
    generated_code: str | None
    is_valid: int
    result_summary: str | None
    created_at: str | None


# ── Endpoints ─────────────────────────────────────────────

@router.post("/ask")
def ask_query(
    req: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Full query pipeline — each request is independent.
    No global state is reused between calls.

    Steps:
    1. Load dataset (fresh read)
    2. Generate Pandas code via LLM
    3. Validate the generated code
    4. Execute on in-memory copy
    5. Select visualization type (with optional override)
    6. Generate insights
    7. Log to database
    """
    # ── 1. Load dataset (with ownership check) ────────────
    dataset = _get_user_dataset(req.dataset_id, current_user.id)

    df = load_dataframe(dataset["filepath"])
    schema_summary = dataset["schema_summary"]
    column_names = [col["name"] for col in dataset["schema"]["columns"]]

    # ── 2. Generate code via LLM (with optional context) ────
    context_str = None
    if req.session_id:
        context_str = build_context_string(
            req.session_id, dataset_id=req.dataset_id, db=db
        )

    llm_result = llm_engine.generate_code(req.query, schema_summary, context_str)
    generated_code = llm_result["code"]
    explanation = llm_result["explanation"]

    # ── 3. Validate the generated code ────────────────────
    validation = validate_query(generated_code, column_names)
    if not validation["is_valid"]:
        # Log the failed query
        log_query(
            db=db,
            user_id=current_user.id,
            natural_query=req.query,
            generated_code=generated_code,
            is_valid=False,
            result_summary=json.dumps({"errors": validation["errors"]}),
        )
        return {
            "success": False,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "generated_code": generated_code,
        }

    # ── 4. Execute on in-memory copy ──────────────────────
    exec_result = execute_query(df, generated_code)
    if not exec_result["success"]:
        log_query(
            db=db,
            user_id=current_user.id,
            natural_query=req.query,
            generated_code=generated_code,
            is_valid=True,
            result_summary=json.dumps({"error": exec_result["error"]}),
        )
        return {
            "success": False,
            "errors": [exec_result["error"]],
            "generated_code": generated_code,
        }

    # ── 5. Select visualization (with optional override) ──
    viz = select_visualization(
        data=exec_result["data"],
        columns=exec_result["columns"],
        row_count=exec_result["row_count"],
        graph_type=req.graph_type,
    )

    # ── 6. Generate insights ──────────────────────────────
    insights = generate_insights(
        data=exec_result["data"],
        columns=exec_result["columns"],
    )

    # ── 6b. Anomaly detection (configurable thresholds) ─────────
    anomalies = detect_anomalies(
        data=exec_result["data"],
        columns=exec_result["columns"],
        z_threshold=req.z_threshold or 3.0,
        iqr_multiplier=req.iqr_multiplier or 1.5,
    )

    # ── 6c. AI Narration (Gemini prose summary) ───────────
    result_summary = insights.get("summary", "")
    highlights = insights.get("highlights", [])
    narration = llm_engine.generate_narration(
        query=req.query,
        result_summary=result_summary,
        highlights=highlights,
    )

    # ── 6d. Suggested Follow-up Questions ─────────────────
    suggestions = llm_engine.generate_suggestions(
        query=req.query,
        schema_summary=schema_summary,
        result_summary=result_summary[:300],
    )

    # ── 7. Log the successful query ───────────────────────
    summary_text = insights.get("summary", "")[:200] if isinstance(insights.get("summary"), str) else ""
    log_query(
        db=db,
        user_id=current_user.id,
        natural_query=req.query,
        generated_code=generated_code,
        is_valid=True,
        result_summary=json.dumps(summary_text),
    )

    # ── 7b. Save to session context (scoped by dataset) ──
    if req.session_id:
        add_to_context(
            session_id  = req.session_id,
            dataset_id  = req.dataset_id,
            query       = req.query,
            code        = generated_code,
            explanation = explanation,
            user_id     = current_user.id,
            db          = db,
        )

    # ── Return fresh result ──────────────────────────────
    return {
        "success": True,
        "query": req.query,
        "generated_code": generated_code,
        "explanation": explanation,
        "validation_warnings": validation["warnings"],
        "result": {
            "data": exec_result["data"],
            "columns": exec_result["columns"],
            "row_count": exec_result["row_count"],
        },
        "visualization": viz,
        "insights": insights,
        "anomalies": anomalies,
        "narration": narration,
        "suggestions": suggestions,
    }


@router.post("/clean")
def clean_dataset(
    req: CleanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Natural Language Data Cleaning — converts a plain-English cleaning
    instruction into Pandas code, validates it, and executes it.

    If persist=True (default), the cleaned DataFrame is written back
    to disk so subsequent queries use the cleaned version.

    Examples:
      - "remove duplicate rows"
      - "fill missing values with 0"
      - "drop rows where age is null"
      - "convert price column to numeric"
    """
    dataset = _get_user_dataset(req.dataset_id, current_user.id)
    datasets = get_dataset_store()

    df = load_dataframe(dataset["filepath"])
    schema_summary = dataset["schema_summary"]
    column_names = [col["name"] for col in dataset["schema"]["columns"]]

    # Build a targeted cleaning prompt
    cleaning_prompt = (
        f"Dataset columns: {', '.join(column_names)}\n"
        f"Task: {req.instruction}\n"
        f"Write a single Pandas expression that cleans the dataframe `df` as instructed. "
        f"The result must be a DataFrame (not a Series or scalar). "
        f"For fillna with mean/median, use: "
        f"df.fillna(df.select_dtypes(include='number').mean()) "
        f"Only return the code, no explanation."
    )

    llm_result = llm_engine.generate_code(cleaning_prompt, schema_summary)
    generated_code = llm_result["code"]

    # Validate
    validation = validate_query(generated_code, column_names)
    if not validation["is_valid"]:
        return {
            "success": False,
            "errors": validation["errors"],
            "generated_code": generated_code,
        }

    # ── Execute cleaning DIRECTLY on full DataFrame (not via execute_query
    #    which truncates to 500 rows and would destroy data on persist)
    import pandas as _pd

    before_rows = len(df)

    try:
        df_copy = df.copy()
        exec_ns = {"df": df_copy, "pd": _pd}
        # Try as expression first (e.g., df.fillna(...))
        try:
            cleaned_df = eval(generated_code, {"__builtins__": {}}, exec_ns)
        except SyntaxError:
            # If it's a statement (e.g., df['col'] = ...), exec it
            exec(generated_code, {"__builtins__": {}}, exec_ns)
            cleaned_df = exec_ns["df"]

        # Ensure result is a DataFrame
        if isinstance(cleaned_df, _pd.Series):
            cleaned_df = cleaned_df.to_frame()
        elif not isinstance(cleaned_df, _pd.DataFrame):
            return {
                "success": False,
                "errors": ["Cleaning operation did not return a DataFrame"],
                "generated_code": generated_code,
            }
    except Exception as e:
        return {
            "success": False,
            "errors": [f"Execution error: {str(e)}"],
            "generated_code": generated_code,
        }

    after_rows = len(cleaned_df)

    # ── Persist cleaned data back to disk ──────────────────
    if req.persist:
        try:
            filepath = dataset["filepath"]

            # Write back to the same file format
            if filepath.endswith(".csv"):
                cleaned_df.to_csv(filepath, index=False)
            elif filepath.endswith((".xlsx", ".xls")):
                cleaned_df.to_excel(filepath, index=False)

            # Update in-memory schema and profile
            new_schema = extract_schema(cleaned_df)
            new_summary = generate_schema_summary(new_schema)
            new_profile = create_data_profile(cleaned_df)

            datasets[req.dataset_id]["schema"] = new_schema
            datasets[req.dataset_id]["schema_summary"] = new_summary
            datasets[req.dataset_id]["profile"] = new_profile
        except Exception:
            pass  # Non-fatal: cleaning result is still returned

    # Build a small preview from the cleaned data
    import json as _json
    preview_data = _json.loads(
        cleaned_df.head(10).fillna("").to_json(orient="records", date_format="iso")
    )

    return {
        "success": True,
        "instruction": req.instruction,
        "generated_code": generated_code,
        "before_rows": before_rows,
        "after_rows": after_rows,
        "rows_removed": before_rows - after_rows,
        "preview": preview_data,
        "columns": list(cleaned_df.columns),
        "persisted": req.persist,
    }


@router.post("/forecast")
def forecast_query(
    req: ForecastRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Predictive Analytics — forecast future values using
    linear regression or moving average.
    """
    dataset = _get_user_dataset(req.dataset_id, current_user.id)

    df = load_dataframe(dataset["filepath"])

    # Run the query first to get grouped/aggregated data if needed
    data = df.to_dict("records")
    columns = list(df.columns)

    # If columns don't exist, return error
    if req.x_column not in columns or req.y_column not in columns:
        raise HTTPException(
            status_code=400,
            detail=f"Columns '{req.x_column}' or '{req.y_column}' not found. Available: {columns}"
        )

    result = forecast(
        data=data,
        x_column=req.x_column,
        y_column=req.y_column,
        periods=req.periods or 5,
        method=req.method or "linear",
    )

    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {
        "success": True,
        "x_column": req.x_column,
        "y_column": req.y_column,
        **result,
    }


@router.get("/history")
def query_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated user's query history."""
    entries = get_user_history(db, user_id=current_user.id)
    return [
        {
            "id": e.id,
            "natural_query": e.natural_query,
            "generated_code": e.generated_code,
            "is_valid": e.is_valid,
            "result_summary": e.result_summary,
            "created_at": str(e.created_at) if e.created_at else None,
        }
        for e in entries
    ]
