"""
============================================================
Datasets API — Upload, validate, and inspect datasets
============================================================
Endpoints:
  POST /api/datasets/upload   → Upload and validate a file
  GET  /api/datasets/{id}/schema → Get extracted schema
  GET  /api/datasets/{id}/profile → Get data profile
============================================================
"""

import os
import json
import threading

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from database.session import get_db
from database.models import User, DatasetRecord
from core.config import settings
from utils.helpers import ensure_directory, generate_filename
from services.data_validator import (
    validate_file_format, load_dataframe, create_data_profile,
)
from services.schema_extractor import extract_schema, generate_schema_summary
from services.data_profiler import generate_full_profile

router = APIRouter()

# ── In-memory dataset storage ─────────────────────────────
_datasets: dict = {}
_dataset_counter = 0
_counter_lock = threading.Lock()  # Gap 8: prevents race condition


# ── Dataset ownership verification ────────────────────────
def _verify_dataset_access(dataset_id: str, user_id: int) -> dict:
    """
    Check that the dataset exists in memory AND belongs to the user.
    Raises HTTPException if not found or not authorized.
    Returns the dataset dict if access is valid.
    """
    if dataset_id not in _datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    dataset = _datasets[dataset_id]
    if dataset.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorised to access this dataset",
        )
    return dataset


def restore_datasets_from_db():
    """
    Called on server startup — reloads all active dataset records
    from Neon DB back into the in-memory store so that previously
    uploaded datasets survive server restarts without re-uploading.
    """
    global _dataset_counter
    from database.session import SessionLocal
    import logging
    log = logging.getLogger(__name__)
    try:
        db = SessionLocal()
        records = db.query(DatasetRecord).filter(DatasetRecord.is_active == True).all()
        restored = 0
        for r in records:
            if not os.path.exists(r.filepath):
                log.warning("Dataset file missing, skipping: %s", r.filepath)
                continue
            try:
                df = load_dataframe(r.filepath)
                schema = extract_schema(df)
                schema_summary = r.schema_summary or generate_schema_summary(schema)
                _datasets[r.dataset_id] = {
                    "filepath":       r.filepath,
                    "filename":       r.filename,
                    "schema":         schema,
                    "schema_summary": schema_summary,
                    "profile":        {},
                    "user_id":        r.user_id,
                }
                # Keep counter in sync
                try:
                    num = int(r.dataset_id)
                    if num > _dataset_counter:
                        _dataset_counter = num
                except ValueError:
                    pass
                restored += 1
            except Exception as exc:
                log.warning("Could not restore dataset %s: %s", r.dataset_id, exc)
        db.close()
        log.info("Restored %d/%d datasets from DB into memory", restored, len(records))
    except Exception as exc:
        log.warning("Dataset restore failed (non-fatal): %s", exc)


# ── Lazy restore flag ─────────────────────────────────────
_restored = False


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV or Excel file.
    Validates format, creates data profile, extracts schema.
    """
    global _dataset_counter

    # ── Validate file format ──────────────────────────────
    if not validate_file_format(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload CSV or Excel (.xlsx/.xls).",
        )

    # ── Save file to datasets/ directory ──────────────────
    upload_dir = ensure_directory(settings.UPLOAD_DIR)
    safe_name = generate_filename(file.filename, prefix=f"user{current_user.id}_")
    filepath = os.path.join(upload_dir, safe_name)

    contents = await file.read()
    # Check file size
    if len(contents) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

    with open(filepath, "wb") as f:
        f.write(contents)

    # ── Load and process ──────────────────────────────────
    try:
        df = load_dataframe(filepath)
    except Exception as e:
        os.remove(filepath)
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # ── Data profile and schema ───────────────────────────
    profile = create_data_profile(df)
    schema = extract_schema(df)
    schema_summary = generate_schema_summary(schema)

    # ── Thread-safe counter increment ─────────────────────
    with _counter_lock:
        _dataset_counter += 1
        dataset_id = str(_dataset_counter)

    _datasets[dataset_id] = {
        "filepath":       filepath,
        "filename":       file.filename,
        "schema":         schema,
        "schema_summary": schema_summary,
        "profile":        profile,
        "user_id":        current_user.id,
    }

    # ── Persist metadata to DB ────────────────────────────
    try:
        record = DatasetRecord(
            user_id        = current_user.id,
            dataset_id     = dataset_id,
            filename       = file.filename,
            filepath       = filepath,
            row_count      = len(df),
            column_count   = len(df.columns),
            schema_summary = schema_summary,
        )
        db.add(record)
        db.commit()
    except Exception:
        pass  # Non-fatal: in-memory store still works

    return {
        "dataset_id":   dataset_id,
        "filename":     file.filename,
        "row_count":    len(df),
        "column_count": len(df.columns),
        "profile":      profile,
        "schema":       schema,
        "message":      "Dataset uploaded and validated successfully",
    }


@router.get("/{dataset_id}/schema")
def get_schema(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the extracted schema for a dataset."""
    dataset = _verify_dataset_access(dataset_id, current_user.id)
    return dataset["schema"]


@router.get("/{dataset_id}/profile")
def get_profile(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the data validation profile for a dataset."""
    dataset = _verify_dataset_access(dataset_id, current_user.id)
    return dataset["profile"]


def get_dataset_store():
    """
    Expose dataset store for use by other modules.
    Performs a one-time lazy restore from Neon DB on first call
    so datasets survive server restarts without re-uploading.
    """
    global _restored
    if not _restored:
        _restored = True
        restore_datasets_from_db()
    return _datasets


@router.get("/list")
def list_my_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all dataset records uploaded by the current user.
    Includes datasets from past sessions (stored in DB).
    """
    records = (
        db.query(DatasetRecord)
        .filter(
            DatasetRecord.user_id  == current_user.id,
            DatasetRecord.is_active == True,
        )
        .order_by(DatasetRecord.uploaded_at.desc())
        .all()
    )
    return [
        {
            "dataset_id":   r.dataset_id,
            "filename":     r.filename,
            "row_count":    r.row_count,
            "column_count": r.column_count,
            "uploaded_at":  str(r.uploaded_at) if r.uploaded_at else None,
            "in_memory":    r.dataset_id in _datasets,
        }
        for r in records
    ]


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Soft-delete a dataset: sets is_active=False in DB and removes
    it from the in-memory store so it no longer appears in pickers.
    Only the owner of the dataset can delete it.
    """
    # ── DB record ─────────────────────────────────────────
    record = (
        db.query(DatasetRecord)
        .filter(
            DatasetRecord.dataset_id == dataset_id,
            DatasetRecord.is_active == True,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to delete this dataset")

    # Soft-delete in DB
    record.is_active = False
    db.commit()

    # Remove from in-memory store
    _datasets.pop(dataset_id, None)

    return {"success": True, "dataset_id": dataset_id, "message": "Dataset deleted successfully"}


@router.get("/{dataset_id}/full-profile")
def get_full_profile(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a rich data profile with stats, correlations, and top values."""
    dataset = _verify_dataset_access(dataset_id, current_user.id)

    from services.data_validator import load_dataframe as _load_df
    df = _load_df(dataset["filepath"])
    profile = generate_full_profile(df)
    return profile


# ── Export endpoint with proper Pydantic schema ───────────

class ExportRequest(BaseModel):
    """Validated request body for Excel export."""
    data: List[Dict[str, Any]]
    columns: List[str] = []
    filename: Optional[str] = "export.xlsx"


@router.post("/export-excel")
def export_excel(
    payload: ExportRequest,
    current_user: User = Depends(get_current_user),
):
    """Export query result data as an Excel file."""
    from services.report_exporter import export_to_excel
    from fastapi.responses import Response

    xlsx_bytes = export_to_excel(payload.data, payload.columns)

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{payload.filename}"'},
    )
