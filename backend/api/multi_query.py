"""
============================================================
Multi-Query API — JOIN queries across two datasets
============================================================
Endpoint:
  POST /api/multi-query/ask

Pipeline:
  Load DF1 + DF2 → merge on join_col → run full query
  pipeline (same as /api/queries/ask) on merged result

  Also provides:
  GET /api/multi-query/preview-join  → merged preview (no query)
============================================================
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

import pandas as pd

from auth.jwt_handler import get_current_user
from database.session import get_db
from database.models import User
from services.data_validator import load_dataframe
from services.query_validator import validate_query
from services.query_executor import execute_query
from services.viz_selector import select_visualization
from services.insight_generator import generate_insights
from services.anomaly_detector import detect_anomalies
from services.query_logger import log_query
from services.context_manager import add_to_context, build_context_string
from services.schema_extractor import extract_schema, generate_schema_summary
from llm.llm_engine import llm_engine
from api.datasets import get_dataset_store

router = APIRouter()


# ── Request schemas ────────────────────────────────────────

class JoinQueryRequest(BaseModel):
    dataset_id_1: str
    dataset_id_2: str
    join_on:      str               # column name present in BOTH datasets
    join_how:     Optional[str] = "inner"   # inner | left | right | outer
    query:        str
    graph_type:   Optional[str]   = "auto"
    session_id:   Optional[str]   = None
    z_threshold:  Optional[float] = 3.0
    iqr_multiplier: Optional[float] = 1.5


class JoinPreviewRequest(BaseModel):
    dataset_id_1: str
    dataset_id_2: str
    join_on:      str
    join_how:     Optional[str] = "inner"


# ── Helpers ────────────────────────────────────────────────

def _verify_dataset(datasets, dataset_id: str, user_id: int) -> dict:
    """Verify a dataset exists and belongs to the user."""
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    ds = datasets[dataset_id]
    if ds.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail=f"Not authorised to access dataset '{dataset_id}'")
    return ds


def _load_and_merge(datasets, id1: str, id2: str, join_on: str, how: str, user_id: int) -> pd.DataFrame:
    """Load two datasets (with ownership check) and merge them on the specified column."""
    ds1 = _verify_dataset(datasets, id1, user_id)
    ds2 = _verify_dataset(datasets, id2, user_id)

    df1 = load_dataframe(ds1["filepath"])
    df2 = load_dataframe(ds2["filepath"])

    if join_on not in df1.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Column '{join_on}' not found in dataset '{id1}'. "
                   f"Available: {', '.join(df1.columns.tolist())}",
        )
    if join_on not in df2.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Column '{join_on}' not found in dataset '{id2}'. "
                   f"Available: {', '.join(df2.columns.tolist())}",
        )

    # Suffix overlapping columns (except the join key) to avoid ambiguity
    merged = pd.merge(df1, df2, on=join_on, how=how, suffixes=("_1", "_2"))
    return merged


# ── Endpoints ──────────────────────────────────────────────

@router.post("/ask")
def multi_query_ask(
    req: JoinQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run a natural-language query on the JOINED result of two datasets.

    Steps:
    1. Load both datasets
    2. Merge on join_on column
    3. Build a combined schema summary
    4. Run the full query pipeline on the merged DataFrame
    """
    datasets = get_dataset_store()

    # ── 1+2. Load & merge (with ownership check) ─────────
    merged_df = _load_and_merge(
        datasets, req.dataset_id_1, req.dataset_id_2,
        req.join_on, req.join_how, current_user.id,
    )

    # ── 3. Build combined schema summary (proper format) ──
    # Gap 7: Use extract_schema + generate_schema_summary instead
    # of raw dtype strings, and don't truncate columns.
    merged_schema = extract_schema(merged_df)
    schema_summary = (
        f"Merged dataset ({len(merged_df)} rows, {len(merged_df.columns)} columns). "
        f"Joined on '{req.join_on}' using {req.join_how} join.\n"
        + generate_schema_summary(merged_schema)
    )
    cols = merged_df.columns.tolist()

    # ── 4. LLM code generation ────────────────────────────
    context_str = None
    if req.session_id:
        context_str = build_context_string(req.session_id, db=db)

    llm_result     = llm_engine.generate_code(req.query, schema_summary, context_str)
    generated_code = llm_result["code"]
    explanation    = llm_result["explanation"]

    # ── 5. Validate ───────────────────────────────────────
    validation = validate_query(generated_code, cols)
    if not validation["is_valid"]:
        log_query(db=db, user_id=current_user.id, natural_query=req.query,
                  generated_code=generated_code, is_valid=False,
                  result_summary=json.dumps({"errors": validation["errors"]}))
        return {"success": False, "errors": validation["errors"],
                "generated_code": generated_code}

    # ── 6. Execute ────────────────────────────────────────
    exec_result = execute_query(merged_df, generated_code)
    if not exec_result["success"]:
        log_query(db=db, user_id=current_user.id, natural_query=req.query,
                  generated_code=generated_code, is_valid=True,
                  result_summary=json.dumps({"error": exec_result["error"]}))
        return {"success": False, "errors": [exec_result["error"]],
                "generated_code": generated_code}

    # ── 7. Viz + Insights + Narration ─────────────────────
    viz      = select_visualization(exec_result["data"], exec_result["columns"],
                                    exec_result["row_count"], req.graph_type)
    insights = generate_insights(exec_result["data"], exec_result["columns"])
    anomalies = detect_anomalies(exec_result["data"], exec_result["columns"],
                                 req.z_threshold or 3.0, req.iqr_multiplier or 1.5)
    narration = llm_engine.generate_narration(req.query, insights.get("summary",""),
                                              insights.get("highlights",[]))
    suggestions = llm_engine.generate_suggestions(req.query, schema_summary,
                                                   insights.get("summary","")[:300])

    # ── 8. Log ───────────────────────────────────────────
    log_query(db=db, user_id=current_user.id, natural_query=req.query,
              generated_code=generated_code, is_valid=True,
              result_summary=json.dumps(insights.get("summary","")[:200]))

    if req.session_id:
        add_to_context(session_id=req.session_id, query=req.query,
                       code=generated_code, explanation=explanation,
                       user_id=current_user.id, db=db)

    return {
        "success": True,
        "query": req.query,
        "join_info": {
            "dataset_1": req.dataset_id_1,
            "dataset_2": req.dataset_id_2,
            "join_on":   req.join_on,
            "join_how":  req.join_how,
            "merged_rows": len(merged_df),
            "merged_cols": len(cols),
        },
        "generated_code":     generated_code,
        "explanation":        explanation,
        "validation_warnings": validation["warnings"],
        "result": {
            "data":      exec_result["data"],
            "columns":   exec_result["columns"],
            "row_count": exec_result["row_count"],
        },
        "visualization": viz,
        "insights":      insights,
        "anomalies":     anomalies,
        "narration":     narration,
        "suggestions":   suggestions,
    }


@router.post("/preview-join")
def preview_join(
    req: JoinPreviewRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Preview the first 10 rows of the merged DataFrame before running a query.
    Also returns which columns came from each dataset.
    """
    datasets    = get_dataset_store()
    merged_df   = _load_and_merge(datasets, req.dataset_id_1, req.dataset_id_2,
                                  req.join_on, req.join_how, current_user.id)

    cols_ds1    = load_dataframe(datasets[req.dataset_id_1]["filepath"]).columns.tolist()
    cols_ds2    = load_dataframe(datasets[req.dataset_id_2]["filepath"]).columns.tolist()

    preview_data = merged_df.head(10).fillna("").to_dict(orient="records")

    return {
        "merged_rows":   len(merged_df),
        "merged_cols":   len(merged_df.columns),
        "join_on":       req.join_on,
        "join_how":      req.join_how,
        "columns":       merged_df.columns.tolist(),
        "columns_from_ds1": cols_ds1,
        "columns_from_ds2": cols_ds2,
        "preview":       preview_data,
    }


@router.get("/common-columns")
def common_columns(
    dataset_id_1: str,
    dataset_id_2: str,
    current_user: User = Depends(get_current_user),
):
    """
    Return columns that exist in BOTH datasets — these are valid join keys.
    """
    datasets = get_dataset_store()
    _verify_dataset(datasets, dataset_id_1, current_user.id)
    _verify_dataset(datasets, dataset_id_2, current_user.id)

    df1_cols = set(load_dataframe(datasets[dataset_id_1]["filepath"]).columns)
    df2_cols = set(load_dataframe(datasets[dataset_id_2]["filepath"]).columns)
    common   = sorted(df1_cols & df2_cols)

    return {
        "common_columns":  common,
        "dataset_1_cols":  sorted(df1_cols),
        "dataset_2_cols":  sorted(df2_cols),
    }
