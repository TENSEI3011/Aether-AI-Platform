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

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from database.session import get_db
from database.models import User
from core.config import settings
from utils.helpers import ensure_directory, generate_filename
from services.data_validator import (
    validate_file_format, load_dataframe, create_data_profile,
)
from services.schema_extractor import extract_schema, generate_schema_summary

router = APIRouter()

# ── In-memory dataset storage ─────────────────────────────
# Maps dataset_id → {"filepath": str, "schema": dict, "profile": dict}
# In production, use a database or object store.
_datasets: dict = {}
_dataset_counter = 0


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

    # ── Store in memory ───────────────────────────────────
    _dataset_counter += 1
    dataset_id = str(_dataset_counter)
    _datasets[dataset_id] = {
        "filepath": filepath,
        "filename": file.filename,
        "schema": schema,
        "schema_summary": schema_summary,
        "profile": profile,
        "user_id": current_user.id,
    }

    return {
        "dataset_id": dataset_id,
        "filename": file.filename,
        "profile": profile,
        "schema": schema,
        "message": "Dataset uploaded and validated successfully",
    }


@router.get("/{dataset_id}/schema")
def get_schema(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the extracted schema for a dataset."""
    if dataset_id not in _datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return _datasets[dataset_id]["schema"]


@router.get("/{dataset_id}/profile")
def get_profile(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the data validation profile for a dataset."""
    if dataset_id not in _datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return _datasets[dataset_id]["profile"]


def get_dataset_store():
    """Expose dataset store for use by other modules."""
    return _datasets
