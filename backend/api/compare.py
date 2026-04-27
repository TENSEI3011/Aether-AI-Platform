"""
============================================================
Compare API — Side-by-side dataset comparison
============================================================
Endpoints:
  POST /api/compare → Compare two datasets and return diff
============================================================
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from database.session import get_db
from database.models import User
from services.data_validator import load_dataframe
from services.data_differ import compare_datasets
from api.datasets import _datasets as datasets_store

router = APIRouter()


class CompareRequest(BaseModel):
    dataset_id_1: str   # "before" dataset
    dataset_id_2: str   # "after" dataset


@router.post("")
def compare(
    req: CompareRequest,
    current_user: User = Depends(get_current_user),
):
    """Compare two datasets and return a structured diff report."""

    # Validate dataset_1
    if req.dataset_id_1 not in datasets_store:
        raise HTTPException(status_code=404, detail=f"Dataset {req.dataset_id_1} not found")
    ds1 = datasets_store[req.dataset_id_1]
    if ds1.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to access dataset 1")

    # Validate dataset_2
    if req.dataset_id_2 not in datasets_store:
        raise HTTPException(status_code=404, detail=f"Dataset {req.dataset_id_2} not found")
    ds2 = datasets_store[req.dataset_id_2]
    if ds2.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to access dataset 2")

    # Load DataFrames
    df1 = load_dataframe(ds1["filepath"])
    df2 = load_dataframe(ds2["filepath"])

    # Run comparison
    result = compare_datasets(df1, df2)

    return {
        "success": True,
        "dataset_1": {"id": req.dataset_id_1, "filename": ds1["filename"], "rows": len(df1)},
        "dataset_2": {"id": req.dataset_id_2, "filename": ds2["filename"], "rows": len(df2)},
        **result,
    }
