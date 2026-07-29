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

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
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
from api.datasets import get_dataset_store

router = APIRouter()


# ── Request/Response schemas ──────────────────────────────

class QueryRequest(BaseModel):
    dataset_id: str
    query: str  # Natural language query
    graph_type: Optional[str] = "auto"  # Chart override: auto, bar, line, pie, table


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
    # ── 1. Load dataset ───────────────────────────────────
    datasets = get_dataset_store()
    if req.dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found. Please upload a dataset first.")

    dataset = datasets[req.dataset_id]
    df = load_dataframe(dataset["filepath"])
    schema_summary = dataset["schema_summary"]
    column_names = [col["name"] for col in dataset["schema"]["columns"]]

    # ── 2. Generate code via LLM (fresh call) ─────────────
    llm_result = llm_engine.generate_code(req.query, schema_summary)
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
        natural_query=req.query,
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
