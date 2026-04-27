"""
============================================================
Reports API — Scheduled reports & report data generation
============================================================
Endpoints:
  POST   /api/reports/generate     → Generate report data for PDF
  POST   /api/reports/schedule     → Create a scheduled report
  GET    /api/reports/schedules    → List scheduled reports
  DELETE /api/reports/schedules/{id} → Delete a schedule
  POST   /api/reports/send-email   → Send report via email
============================================================
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from database.session import get_db
from database.models import User, ScheduledReport
from services.alert_engine import send_alert_email

router = APIRouter()


class ScheduleRequest(BaseModel):
    dataset_id: str
    query: str
    frequency: str = "daily"    # daily, weekly, monthly
    email: Optional[str] = None


class ReportEmailRequest(BaseModel):
    email: str
    subject: str
    body: str


class ReportDataRequest(BaseModel):
    query: str
    result_data: List[Dict[str, Any]] = []
    columns: List[str] = []
    insights_summary: str = ""
    insights_highlights: List[str] = []
    narration: str = ""
    chart_type: str = ""
    dataset_name: str = ""


@router.post("/generate")
def generate_report_data(
    req: ReportDataRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Structure query results into a report-ready payload.
    The actual PDF is rendered client-side using jsPDF.
    """
    return {
        "success": True,
        "report": {
            "title": f"Analysis Report: {req.query[:60]}",
            "generated_by": current_user.username,
            "dataset": req.dataset_name,
            "query": req.query,
            "chart_type": req.chart_type,
            "data_preview": req.result_data[:50],
            "columns": req.columns,
            "insights": {
                "summary": req.insights_summary,
                "highlights": req.insights_highlights,
            },
            "narration": req.narration,
            "row_count": len(req.result_data),
        },
    }


@router.post("/schedule")
def create_schedule(
    req: ScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a scheduled report."""
    if req.frequency not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Frequency must be: daily, weekly, monthly")

    schedule = ScheduledReport(
        user_id=current_user.id,
        dataset_id=req.dataset_id,
        query=req.query,
        frequency=req.frequency,
        email=req.email or current_user.email,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return {
        "success": True,
        "id": schedule.id,
        "message": f"Report scheduled ({req.frequency})",
    }


@router.get("/schedules")
def list_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all scheduled reports for the current user."""
    schedules = (
        db.query(ScheduledReport)
        .filter(ScheduledReport.user_id == current_user.id)
        .order_by(ScheduledReport.created_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "dataset_id": s.dataset_id,
            "query": s.query,
            "frequency": s.frequency,
            "email": s.email,
            "is_active": s.is_active,
            "last_run": str(s.last_run) if s.last_run else None,
            "created_at": str(s.created_at) if s.created_at else None,
        }
        for s in schedules
    ]


@router.delete("/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a scheduled report."""
    s = db.query(ScheduledReport).filter(ScheduledReport.id == schedule_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if s.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")
    db.delete(s)
    db.commit()
    return {"success": True, "message": "Schedule deleted"}


@router.post("/send-email")
def send_report_email(
    req: ReportEmailRequest,
    current_user: User = Depends(get_current_user),
):
    """Send a report summary via email."""
    sent = send_alert_email(
        to_email=req.email,
        subject=req.subject,
        body=req.body,
    )
    if sent:
        return {"success": True, "message": f"Report sent to {req.email}"}
    return {"success": False, "message": "Email delivery failed. Check SMTP configuration."}
