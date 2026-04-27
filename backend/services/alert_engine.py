"""
============================================================
Alert Engine — Check Smart Alert Rules Against Datasets
============================================================
Evaluates user-defined alert rules (column > threshold, etc.)
against the current dataset data, generates notifications,
and optionally sends email alerts via SMTP.
============================================================
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
from sqlalchemy.orm import Session

from core.config import settings

logger = logging.getLogger(__name__)

# Condition operators
OPERATORS = {
    "gt":  lambda val, thr: val > thr,
    "lt":  lambda val, thr: val < thr,
    "eq":  lambda val, thr: abs(val - thr) < 0.001,
    "gte": lambda val, thr: val >= thr,
    "lte": lambda val, thr: val <= thr,
}

CONDITION_LABELS = {
    "gt": "greater than",
    "lt": "less than",
    "eq": "equal to",
    "gte": "greater than or equal to",
    "lte": "less than or equal to",
}


def check_alerts(
    dataset_id: str,
    user_id: int,
    df: pd.DataFrame,
    db: Session,
) -> List[Dict[str, Any]]:
    """
    Check all active alerts for a user's dataset against the data.

    Returns a list of triggered alert notifications.
    """
    from database.models import SmartAlert, AlertNotification

    alerts = (
        db.query(SmartAlert)
        .filter(
            SmartAlert.user_id == user_id,
            SmartAlert.dataset_id == dataset_id,
            SmartAlert.is_active == True,
        )
        .all()
    )

    triggered = []

    for alert in alerts:
        col = alert.column_name
        if col not in df.columns:
            continue

        if not pd.api.types.is_numeric_dtype(df[col]):
            continue

        op_fn = OPERATORS.get(alert.condition)
        if not op_fn:
            continue

        # Check if any value in the column triggers the alert
        series = df[col].dropna()
        triggered_values = series[series.apply(lambda v: op_fn(v, alert.threshold))]

        if len(triggered_values) > 0:
            cond_label = CONDITION_LABELS.get(alert.condition, alert.condition)
            count = len(triggered_values)
            sample_val = round(float(triggered_values.iloc[0]), 2)
            max_val = round(float(triggered_values.max()), 2)
            min_val = round(float(triggered_values.min()), 2)

            message = (
                f"🔔 Alert: {count} value(s) in '{col}' are {cond_label} {alert.threshold}. "
                f"Range: {min_val} – {max_val} (sample: {sample_val})."
            )

            # Create notification
            notification = AlertNotification(
                alert_id=alert.id,
                user_id=user_id,
                message=message,
            )
            db.add(notification)

            # Update last_triggered
            alert.last_triggered = datetime.utcnow()

            triggered.append({
                "alert_id": alert.id,
                "label": alert.label or f"{col} {cond_label} {alert.threshold}",
                "message": message,
                "count": count,
                "column": col,
                "condition": alert.condition,
                "threshold": alert.threshold,
            })

    if triggered:
        db.commit()

    return triggered


def send_alert_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an alert notification email via SMTP.
    Returns True if sent successfully, False otherwise.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.info("SMTP not configured — skipping email delivery")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
        msg["To"] = to_email

        # HTML email body
        html_body = f"""
        <html>
        <body style="font-family: 'Inter', Arial, sans-serif; background: #0E0E13; color: #E4E1E9; padding: 2rem;">
            <div style="max-width: 600px; margin: 0 auto; background: #1F1F25; border-radius: 16px; padding: 2rem; border: 1px solid rgba(124,58,237,0.2);">
                <h2 style="color: #D2BBFF; margin-bottom: 1rem;">🧠 AI Analysis Platform</h2>
                <div style="background: #2A292F; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
                    {body}
                </div>
                <p style="color: #958DA1; font-size: 0.85rem; margin-top: 1.5rem;">
                    This is an automated notification from your AI Analysis Platform.
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], [to_email], msg.as_string())

        logger.info("Alert email sent to %s", to_email)
        return True

    except Exception as e:
        logger.warning("Failed to send alert email: %s", e)
        return False
