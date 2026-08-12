"""
============================================================
Queries API — Natural language query pipeline
============================================================
Endpoints:
  POST /api/queries/ask        → Process a natural language query
  GET  /api/queries/history    → Get query history
  POST /api/queries/anomalies  → Run anomaly detection
  POST /api/queries/cluster    → Run K-Means clustering
  POST /api/queries/forecast   → Run time-series forecasting
  DELETE /api/queries/memory   → Clear conversation memory

Pipeline:
  NL Query → Semantic Enrich → LLM (generate code) → Validate
  → Execute (with self-correction retry) → Select Viz
  → Generate Insights → Log → Return

ENHANCEMENTS:
  ✅ Self-Correction Retry Loop  (up to MAX_RETRIES attempts)
  ✅ Conversation Memory session (keyed by dataset_id + user_id)
  ✅ Semantic column enrichment   (via llm_engine)
  ✅ Anomaly Detection endpoint   (Isolation Forest)
  ✅ Clustering endpoint          (K-Means)
  ✅ Forecasting endpoint         (Prophet / linear trend)
============================================================
"""

import json
import logging

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from database.session import get_db
from database.models import User
from services.data_validator import load_dataframe
from services.query_validator import validate_query
from services.query_executor import execute_query
from services.viz_selector import select_visualization
from services.insight_generator import generate_insights
from services.query_logger import log_query, get_user_history
from llm.llm_engine import llm_engine
from api.datasets import get_dataset_store, _get_dataset_or_404

# ── New ML services ───────────────────────────────────────
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

try:
    from services.forecaster import forecast_series, detect_datetime_and_numeric
    _FORECAST_AVAILABLE = True
except ImportError:
    _FORECAST_AVAILABLE = False

router = APIRouter()

# ── Constants ─────────────────────────────────────────────
MAX_RETRIES = 3   # Self-correction retry attempts


# ── Request/Response schemas ──────────────────────────────

class QueryRequest(BaseModel):
    dataset_id: str
    query: str          # Natural language query
    graph_type: Optional[str] = "auto"  # Chart override: auto, bar, line, pie, table
    session_id: Optional[str] = None    # For conversation memory (defaults to dataset_id)


class AnomalyRequest(BaseModel):
    dataset_id: str
    contamination: float = 0.05        # Expected anomaly proportion (0.01–0.5)
    numeric_cols: Optional[List[str]] = None


class ClusterRequest(BaseModel):
    dataset_id: str
    numeric_cols: Optional[List[str]] = None
    max_k: int = 8
    label_col: Optional[str] = None    # Categorical col to describe clusters


class ForecastRequest(BaseModel):
    dataset_id: str
    date_col: Optional[str] = None     # Auto-detected if None
    value_col: Optional[str] = None    # Auto-detected if None
    periods: int = 30
    freq: str = "D"                    # D=daily, W=weekly, M=monthly


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
    Full query pipeline with self-correction retry loop.

    Steps:
    1. Load dataset
    2. Generate Pandas code via LLM (with conversation memory + semantic enrichment)
    3. Validate code
    4. Execute on in-memory copy (retry with self-correction on failure)
    5. Select visualization type
    6. Generate insights
    7. Log to database
    """
    # ── 1. Load dataset (with ownership check) ───────────
    datasets = get_dataset_store(db)
    if req.dataset_id not in datasets:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found. Please upload a dataset first.",
        )
    # Enforce ownership — raises 403 if this dataset belongs to another user
    _get_dataset_or_404(req.dataset_id, current_user.id, db)

    dataset = datasets[req.dataset_id]
    df = load_dataframe(dataset["filepath"])
    schema_summary = dataset["schema_summary"]
    column_names = [col["name"] for col in dataset["schema"]["columns"]]

    # ── Determine session ID for conversation memory ───────
    session_id = req.session_id or f"{current_user.id}_{req.dataset_id}"

    # ── 2–4. Generate → Validate → Execute (with retry) ──
    generated_code = None
    explanation = None
    validation = None
    exec_result = None
    attempt = 0
    last_error = None

    while attempt < MAX_RETRIES:
        attempt += 1

        # ── 2. Generate code via LLM ──────────────────────
        if attempt == 1:
            # First attempt: normal generation
            llm_result = llm_engine.generate_code(
                req.query,
                schema_summary,
                column_names=column_names,
                session_id=session_id,
            )
        else:
            # Retry: self-correction with error feedback
            logger.info("QueryPipeline: Retry %d/%d — correcting code", attempt, MAX_RETRIES)
            llm_result = llm_engine.generate_code_with_correction(
                req.query,
                schema_summary,
                error_message=last_error,
                previous_code=generated_code,
                column_names=column_names,
                session_id=session_id,
            )

        generated_code = llm_result["code"]
        explanation = llm_result["explanation"]

        # ── 3. Validate ───────────────────────────────────
        validation = validate_query(generated_code, column_names)
        if not validation["is_valid"]:
            last_error = "; ".join(validation["errors"])
            if attempt == MAX_RETRIES:
                break
            continue

        # ── 4. Execute ────────────────────────────────────
        exec_result = execute_query(df, generated_code)
        if not exec_result["success"]:
            last_error = exec_result["error"]
            if attempt == MAX_RETRIES:
                break
            continue

        # ── Success — break out of retry loop ─────────────
        break

    # ── Handle all-retries-failed ─────────────────────────
    if not validation or not validation["is_valid"]:
        log_query(
            db=db, user_id=current_user.id,
            natural_query=req.query, generated_code=generated_code,
            is_valid=False,
            result_summary=json.dumps({"errors": validation["errors"] if validation else [last_error]}),
        )
        return {
            "success": False,
            "errors": validation["errors"] if validation else [last_error],
            "warnings": validation["warnings"] if validation else [],
            "generated_code": generated_code,
            "retries": attempt,
        }

    if not exec_result or not exec_result["success"]:
        log_query(
            db=db, user_id=current_user.id,
            natural_query=req.query, generated_code=generated_code,
            is_valid=True,
            result_summary=json.dumps({"error": last_error}),
        )
        return {
            "success": False,
            "errors": [last_error],
            "generated_code": generated_code,
            "retries": attempt,
        }

    # ── 5. Select visualization ───────────────────────────
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
        natural_query=req.query,
    )

    # ── 7. Log the successful query ───────────────────────
    summary_text = insights.get("summary", "")[:200] if isinstance(insights.get("summary"), str) else ""
    log_query(
        db=db, user_id=current_user.id,
        natural_query=req.query, generated_code=generated_code,
        is_valid=True, result_summary=json.dumps(summary_text),
    )

    # ── Return result ─────────────────────────────────────
    return {
        "success": True,
        "query": req.query,
        "generated_code": generated_code,
        "explanation": explanation,
        "validation_warnings": validation["warnings"],
        "retries": attempt,           # Shows how many attempts it took
        "result": {
            "data": exec_result["data"],
            "columns": exec_result["columns"],
            "row_count": exec_result["row_count"],
        },
        "visualization": viz,
        "insights": insights,
        "session_id": session_id,     # Return so frontend can persist it
    }


@router.delete("/memory")
def clear_memory(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear the conversation memory for a session (start fresh)."""
    session_id = f"{current_user.id}_{dataset_id}"
    llm_engine.clear_memory(session_id)
    return {"message": f"Memory cleared for session: {session_id}"}


@router.post("/anomalies")
def run_anomaly_detection(
    req: AnomalyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Detect anomalies in the dataset using Isolation Forest.
    ML Concept: Unsupervised anomaly detection.
    """
    if not _ANOMALY_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Anomaly detection unavailable. Install scikit-learn.",
        )

    datasets = get_dataset_store(db)
    if req.dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    _get_dataset_or_404(req.dataset_id, current_user.id, db)

    df = load_dataframe(datasets[req.dataset_id]["filepath"])
    result = detect_anomalies(df, req.contamination, req.numeric_cols)

    return {
        "success": True,
        "dataset_id": req.dataset_id,
        "anomaly_result": result,
    }


@router.post("/cluster")
def run_clustering(
    req: ClusterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run K-Means clustering with automatic K selection (Elbow Method).
    ML Concept: Unsupervised learning — K-Means clustering.
    """
    if not _CLUSTER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Clustering unavailable. Install scikit-learn.",
        )

    datasets = get_dataset_store(db)
    if req.dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    _get_dataset_or_404(req.dataset_id, current_user.id, db)

    df = load_dataframe(datasets[req.dataset_id]["filepath"])
    result = cluster_dataframe(df, req.numeric_cols, req.max_k, req.label_col)

    return {
        "success": True,
        "dataset_id": req.dataset_id,
        "cluster_result": result,
    }


@router.post("/forecast")
def run_forecast(
    req: ForecastRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate time-series forecast using Prophet (or linear trend fallback).
    ML Concept: Time-series forecasting.
    """
    if not _FORECAST_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Forecasting unavailable. Install prophet.",
        )

    datasets = get_dataset_store(db)
    if req.dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    _get_dataset_or_404(req.dataset_id, current_user.id, db)

    df = load_dataframe(datasets[req.dataset_id]["filepath"])

    # ── Auto-detect date and value columns if not specified ──
    date_col = req.date_col
    value_col = req.value_col

    if not date_col or not value_col:
        auto = detect_datetime_and_numeric(df)
        if not auto:
            raise HTTPException(
                status_code=400,
                detail="Could not auto-detect datetime and numeric columns. "
                       "Please specify date_col and value_col.",
            )
        date_col = date_col or auto["date_col"]
        value_col = value_col or auto["value_col"]

    result = forecast_series(df, date_col, value_col, req.periods, req.freq)

    return {
        "success": True,
        "dataset_id": req.dataset_id,
        "date_col": date_col,
        "value_col": value_col,
        "forecast_result": result,
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
