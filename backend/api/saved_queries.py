"""
============================================================
Saved Queries API — Save, list, and re-run query templates
============================================================
Endpoints:
  POST   /api/saved-queries         → Save a query template
  GET    /api/saved-queries         → List user's saved queries
  DELETE /api/saved-queries/{id}    → Delete a saved query
============================================================
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from database.session import get_db
from database.models import User, SavedQuery

router = APIRouter()


class SaveQueryRequest(BaseModel):
    name: str
    dataset_id: str
    natural_query: str
    graph_type: Optional[str] = "auto"


@router.post("")
def save_query(
    req: SaveQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a query as a reusable template."""
    # Check for duplicate names
    existing = (
        db.query(SavedQuery)
        .filter(
            SavedQuery.user_id == current_user.id,
            SavedQuery.name == req.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="A saved query with this name already exists.")

    saved = SavedQuery(
        user_id=current_user.id,
        name=req.name,
        dataset_id=req.dataset_id,
        natural_query=req.natural_query,
        graph_type=req.graph_type or "auto",
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)

    return {
        "success": True,
        "id": saved.id,
        "name": saved.name,
        "message": "Query template saved successfully",
    }


@router.get("")
def list_saved_queries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all saved query templates for the current user."""
    queries = (
        db.query(SavedQuery)
        .filter(SavedQuery.user_id == current_user.id)
        .order_by(SavedQuery.created_at.desc())
        .all()
    )
    return [
        {
            "id": q.id,
            "name": q.name,
            "dataset_id": q.dataset_id,
            "natural_query": q.natural_query,
            "graph_type": q.graph_type,
            "created_at": str(q.created_at) if q.created_at else None,
        }
        for q in queries
    ]


@router.delete("/{query_id}")
def delete_saved_query(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a saved query template."""
    saved = db.query(SavedQuery).filter(SavedQuery.id == query_id).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Saved query not found")
    if saved.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    db.delete(saved)
    db.commit()
    return {"success": True, "message": "Saved query deleted"}
