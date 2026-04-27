"""
============================================================
Alerts API — Smart alert rules and notifications
============================================================
Endpoints:
  POST   /api/alerts                        → Create an alert rule
  GET    /api/alerts                        → List user's alerts
  DELETE /api/alerts/{id}                   → Delete an alert
  POST   /api/alerts/check/{dataset_id}    → Manually check alerts
  GET    /api/alerts/notifications          → Get notifications
  POST   /api/alerts/notifications/{id}/read → Mark read
  POST   /api/alerts/notifications/read-all → Mark all read
============================================================
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from database.session import get_db
from database.models import User, SmartAlert, AlertNotification
from services.data_validator import load_dataframe
from services.alert_engine import check_alerts, send_alert_email
from api.datasets import _datasets as datasets_store

router = APIRouter()


class CreateAlertRequest(BaseModel):
    dataset_id: str
    column_name: str
    condition: str        # gt, lt, eq, gte, lte
    threshold: float
    label: Optional[str] = None


@router.post("")
def create_alert(
    req: CreateAlertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new smart alert rule."""
    if req.condition not in ("gt", "lt", "eq", "gte", "lte"):
        raise HTTPException(status_code=400, detail="Condition must be: gt, lt, eq, gte, lte")

    alert = SmartAlert(
        user_id=current_user.id,
        dataset_id=req.dataset_id,
        column_name=req.column_name,
        condition=req.condition,
        threshold=req.threshold,
        label=req.label,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return {
        "success": True,
        "id": alert.id,
        "message": "Alert created successfully",
    }


@router.get("")
def list_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all alert rules for the current user."""
    alerts = (
        db.query(SmartAlert)
        .filter(SmartAlert.user_id == current_user.id)
        .order_by(SmartAlert.created_at.desc())
        .all()
    )
    return [
        {
            "id": a.id,
            "dataset_id": a.dataset_id,
            "column_name": a.column_name,
            "condition": a.condition,
            "threshold": a.threshold,
            "label": a.label,
            "is_active": a.is_active,
            "last_triggered": str(a.last_triggered) if a.last_triggered else None,
            "created_at": str(a.created_at) if a.created_at else None,
        }
        for a in alerts
    ]


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an alert rule and its notifications."""
    alert = db.query(SmartAlert).filter(SmartAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    # Delete associated notifications
    db.query(AlertNotification).filter(AlertNotification.alert_id == alert_id).delete()
    db.delete(alert)
    db.commit()
    return {"success": True, "message": "Alert deleted"}


@router.post("/check/{dataset_id}")
def check_dataset_alerts(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually check all alerts for a dataset."""
    if dataset_id not in datasets_store:
        raise HTTPException(status_code=404, detail="Dataset not found")
    dataset = datasets_store[dataset_id]
    if dataset.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    df = load_dataframe(dataset["filepath"])
    triggered = check_alerts(dataset_id, current_user.id, df, db)

    # Send emails for triggered alerts
    if triggered and current_user.email:
        for t in triggered:
            send_alert_email(
                to_email=current_user.email,
                subject=f"🔔 Alert Triggered: {t['label']}",
                body=t["message"],
            )

    return {
        "success": True,
        "triggered_count": len(triggered),
        "triggered": triggered,
    }


@router.get("/notifications")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all alert notifications for the current user."""
    notifications = (
        db.query(AlertNotification)
        .filter(AlertNotification.user_id == current_user.id)
        .order_by(AlertNotification.created_at.desc())
        .limit(50)
        .all()
    )
    unread_count = (
        db.query(AlertNotification)
        .filter(
            AlertNotification.user_id == current_user.id,
            AlertNotification.is_read == False,
        )
        .count()
    )
    return {
        "unread_count": unread_count,
        "notifications": [
            {
                "id": n.id,
                "alert_id": n.alert_id,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": str(n.created_at) if n.created_at else None,
            }
            for n in notifications
        ],
    }


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a single notification as read."""
    n = db.query(AlertNotification).filter(AlertNotification.id == notification_id).first()
    if not n or n.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return {"success": True}


@router.post("/notifications/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    db.query(AlertNotification).filter(
        AlertNotification.user_id == current_user.id,
        AlertNotification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"success": True}
