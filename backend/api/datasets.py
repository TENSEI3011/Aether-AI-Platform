"""
============================================================
Datasets API — Upload, validate, and inspect datasets
============================================================
Endpoints:
  POST /api/datasets/upload         → Upload and validate a file
  GET  /api/datasets/{id}/schema    → Get extracted schema
  GET  /api/datasets/{id}/profile   → Get data profile
  GET  /api/datasets/               → List all datasets for the user

FIX: Dataset metadata is now persisted to SQLite (Dataset model)
     so uploads survive server restarts. Ownership checks added
     to schema and profile endpoints.
============================================================
"""

import os
import json

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from database.session import get_db
from database.models import User, Dataset
from core.config import settings
from utils.helpers import ensure_directory, generate_filename
from services.data_validator import (
    validate_file_format, load_dataframe, create_data_profile,
)
from services.schema_extractor import extract_schema, generate_schema_summary

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────

def _dataset_to_store_dict(ds: Dataset) -> dict:
    """Convert a Dataset ORM row to the dict shape used by queries."""
    return {
        "filepath":       ds.filepath,
        "filename":       ds.filename,
        "schema":         json.loads(ds.schema_json) if ds.schema_json else {},
        "schema_summary": ds.schema_summary or "",
        "profile":        json.loads(ds.profile_json) if ds.profile_json else {},
        "user_id":        ds.user_id,
    }


def get_dataset_store(db: Session = None):
    """
    Expose dataset store for use by other modules (e.g. api/queries.py).

    Returns a lazy dict-like proxy backed by the DB.
    When db is None (legacy callers), returns an empty dict — callers
    that need real data must pass a db session.
    """
    if db is None:
        return {}
    rows = db.query(Dataset).all()
    return {str(ds.id): _dataset_to_store_dict(ds) for ds in rows}


def _get_dataset_or_404(dataset_id: str, user_id: int, db: Session) -> Dataset:
    """Fetch a dataset, raising 404 if not found and 403 if not owned by user."""
    ds = db.query(Dataset).filter(Dataset.id == int(dataset_id)).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if ds.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied: dataset belongs to another user")
    return ds


# ── Endpoints ─────────────────────────────────────────────

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV or Excel file.
    Validates format, creates data profile, extracts schema.
    Persists dataset metadata to the database so it survives server restarts.
    """
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

    # ── Persist to database ───────────────────────────────
    ds = Dataset(
        user_id=current_user.id,
        filename=file.filename,
        filepath=os.path.abspath(filepath),
        schema_json=json.dumps(schema),
        schema_summary=schema_summary,
        profile_json=json.dumps(profile),
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)

    return {
        "dataset_id": str(ds.id),
        "filename":   file.filename,
        "profile":    profile,
        "schema":     schema,
        "message":    "Dataset uploaded and validated successfully",
    }


@router.get("/")
def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all datasets belonging to the authenticated user."""
    rows = db.query(Dataset).filter(Dataset.user_id == current_user.id).all()
    return [
        {
            "dataset_id": str(ds.id),
            "filename":   ds.filename,
            "created_at": str(ds.created_at) if ds.created_at else None,
        }
        for ds in rows
    ]


@router.get("/{dataset_id}/schema")
def get_schema(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the extracted schema for a dataset (owner only)."""
    ds = _get_dataset_or_404(dataset_id, current_user.id, db)
    return json.loads(ds.schema_json) if ds.schema_json else {}


@router.get("/{dataset_id}/profile")
def get_profile(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the data validation profile for a dataset (owner only)."""
    ds = _get_dataset_or_404(dataset_id, current_user.id, db)
    return json.loads(ds.profile_json) if ds.profile_json else {}
