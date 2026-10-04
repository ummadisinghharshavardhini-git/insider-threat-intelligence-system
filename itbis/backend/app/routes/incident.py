from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident, Employee
from app.risk_scoring import calculate_risk_score


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)


# ============================================================
# CREATE INCIDENT FROM EMPLOYEE RISK
# ============================================================

@router.post("/create-from-risk/{employee_id}")
def create_incident_from_risk(
    employee_id: str,
    db: Session = Depends(get_db)
):

    employee = (
        db.query(Employee)
        .filter(Employee.employee_id == employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    risk = calculate_risk_score(employee_id)

    risk_score = risk["risk_score"]
    risk_level = risk["risk_category"]

    if risk_level not in ["high", "critical"]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Incident can only be created for high or critical risk. "
                f"Current risk level: {risk_level}"
            )
        )

    incident = Incident(
        employee_id=employee_id,
        status="open",
        severity=risk_level,
        summary=(
            f"Investigation required for {employee.name}. "
            f"Current risk score is {risk_score} "
            f"with {risk_level} risk level."
        )
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return {
        "message": "Incident created successfully",
        "incident_id": incident.id,
        "employee_id": employee_id,
        "status": incident.status,
        "severity": incident.severity,
        "risk_score": risk_score,
        "summary": incident.summary,
        "created_at": incident.created_at
    }


# ============================================================
# INCIDENT TIMELINE
# ============================================================

@router.get("/{incident_id}/timeline")
def get_incident_timeline(
    incident_id: int,
    db: Session = Depends(get_db)
):

    # Check incident
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    # MongoDB connection
    from pymongo import MongoClient

    client = MongoClient("mongodb://localhost:27017")
    mongo_db = client["itbis"]

    behavior_logs = mongo_db["behavior_logs"]
    anomaly_logs = mongo_db["anomaly_logs"]

    # Get activity logs
    activities = list(
        behavior_logs.find({
            "employee_id": incident.employee_id
        })
    )

    # Get anomalies
    anomalies = list(
        anomaly_logs.find({
            "employee_id": incident.employee_id,
            "anomaly": True
        })
    )

    timeline = []

    # Add activities
    for activity in activities:

        timestamp = activity.get("timestamp")

        if timestamp:

            timeline.append({
                "type": "activity",
                "timestamp": timestamp,
                "activity": activity.get("activity"),
                "risk_score": activity.get("risk_score", 0),
                "device": activity.get("device"),
                "application": activity.get("application"),
                "data_volume": activity.get("data_volume", 0)
            })

    # Add anomalies
    for anomaly in anomalies:

        detected_at = anomaly.get("detected_at")

        if detected_at:

            timeline.append({
                "type": "anomaly",
                "timestamp": detected_at,
                "activity": anomaly.get("activity"),
                "anomaly": True,
                "login_time_minutes": anomaly.get(
                    "login_time_minutes"
                ),
                "threshold": anomaly.get("threshold")
            })

    # Sort chronologically
    timeline.sort(
        key=lambda item: item["timestamp"]
    )

    client.close()

    return {
        "incident_id": incident.id,
        "employee_id": incident.employee_id,
        "status": incident.status,
        "severity": incident.severity,
        "timeline": timeline
    }