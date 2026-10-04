from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Employee
from app.schemas import AlertCreate


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


@router.post("/")
def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    employee = (
        db.query(Employee)
        .filter(Employee.employee_id == alert_data.employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    allowed_severities = [
        "informational",
        "low",
        "medium",
        "high",
        "critical"
    ]

    if alert_data.severity not in allowed_severities:
        raise HTTPException(
            status_code=400,
            detail="Invalid alert severity"
        )

    alert = Alert(
        employee_id=alert_data.employee_id,
        severity=alert_data.severity,
        message=alert_data.message,
        status="open"
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return {
        "message": "Alert created successfully",
        "alert_id": alert.id,
        "employee_id": alert.employee_id,
        "severity": alert.severity,
        "message_text": alert.message,
        "status": alert.status,
        "assigned_to": alert.assigned_to,
        "created_at": alert.created_at
    }


@router.get("/")
def get_alerts(
    db: Session = Depends(get_db)
):
    alerts = (
        db.query(Alert)
        .order_by(Alert.created_at.desc())
        .all()
    )

    return {
        "alert_count": len(alerts),
        "alerts": [
            {
                "alert_id": alert.id,
                "employee_id": alert.employee_id,
                "severity": alert.severity,
                "message": alert.message,
                "status": alert.status,
                "assigned_to": alert.assigned_to,
                "created_at": alert.created_at
            }
            for alert in alerts
        ]
    }


@router.put("/{alert_id}/assign")
def assign_alert(
    alert_id: int,
    assigned_to: str,
    role: str,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "security_manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin or security_manager can assign alerts"
        )

    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    alert.assigned_to = assigned_to
    alert.status = "assigned"

    db.commit()
    db.refresh(alert)

    return {
        "message": "Alert assigned successfully",
        "alert_id": alert.id,
        "assigned_to": alert.assigned_to,
        "status": alert.status
    }


@router.put("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    role: str,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin or security_analyst can resolve alerts"
        )

    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    alert.status = "resolved"

    db.commit()
    db.refresh(alert)

    return {
        "message": "Alert resolved successfully",
        "alert_id": alert.id,
        "status": alert.status
    }
