from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Employee, Incident, Alert
from app.risk_scoring import calculate_risk_score
from app.ueba import get_risk_trend

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


# ---------------------------------------------------------
# ANALYST DASHBOARD
# ---------------------------------------------------------

@router.get("/analyst")
def analyst_dashboard(
    role: str,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin or security_analyst can access analyst dashboard"
        )

    open_alerts = (
        db.query(Alert)
        .filter(Alert.status.in_(["open", "assigned"]))
        .count()
    )

    active_investigations = (
        db.query(Incident)
        .filter(Incident.status.in_(["open", "investigating"]))
        .count()
    )

    employees = db.query(Employee).all()

    high_risk_employees = []

    for employee in employees:
        risk = calculate_risk_score(employee.employee_id)

        if risk["risk_category"] in ["high", "critical"]:
            high_risk_employees.append({
                "employee_id": employee.employee_id,
                "name": employee.name,
                "risk_score": risk["risk_score"],
                "risk_category": risk["risk_category"]
            })

    return {
        "open_alerts": open_alerts,
        "active_investigations": active_investigations,
        "high_risk_employees": high_risk_employees
    }


# ---------------------------------------------------------
# SOC DASHBOARD
# ---------------------------------------------------------

@router.get("/soc")
def soc_dashboard(
    role: str,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin or security_analyst can access SOC dashboard"
        )

    from pymongo import MongoClient

    client = MongoClient("mongodb://localhost:27017")
    mongo_db = client["itbis"]

    behavior_logs = mongo_db["behavior_logs"]
    anomaly_logs = mongo_db["anomaly_logs"]

    security_events_count = behavior_logs.count_documents({})

    behavioral_anomalies_count = anomaly_logs.count_documents({
        "anomaly": True
    })

    active_investigations = (
        db.query(Incident)
        .filter(
            Incident.status.in_(["open", "investigating"])
        )
        .count()
    )

    recent_threat_intelligence_notes = []

    recent_alerts = (
        db.query(Alert)
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )

    for alert in recent_alerts:
        recent_threat_intelligence_notes.append({
            "alert_id": alert.id,
            "employee_id": alert.employee_id,
            "severity": alert.severity,
            "message": alert.message,
            "status": alert.status,
            "created_at": alert.created_at
        })

    client.close()

    return {
        "security_events_count": security_events_count,
        "behavioral_anomalies_count": behavioral_anomalies_count,
        "active_investigations": active_investigations,
        "recent_threat_intelligence_notes":
            recent_threat_intelligence_notes
    }


# ---------------------------------------------------------
# SECURITY MANAGER DASHBOARD
# ---------------------------------------------------------

@router.get("/security-manager")
def security_manager_dashboard(
    role: str,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "security_manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin or security_manager can access security manager dashboard"
        )

    employees = db.query(Employee).all()

    risk_distribution = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0
    }

    total_risk_score = 0

    for employee in employees:
        risk = calculate_risk_score(employee.employee_id)

        risk_score = risk["risk_score"]
        risk_category = risk["risk_category"]

        total_risk_score += risk_score

        if risk_category in risk_distribution:
            risk_distribution[risk_category] += 1

    total_employees = len(employees)

    if total_employees > 0:
        average_risk_score = round(
            total_risk_score / total_employees,
            1
        )
    else:
        average_risk_score = 0.0

    # ---------------------------------------------
    # Organizational Risk Posture
    # ---------------------------------------------

    if risk_distribution["critical"] > 0:
        organizational_risk_posture = "critical"
    elif risk_distribution["high"] > 0:
        organizational_risk_posture = "high"
    elif risk_distribution["medium"] > 0:
        organizational_risk_posture = "medium"
    else:
        organizational_risk_posture = "low"

    # ---------------------------------------------
    # Risk Trends
    # ---------------------------------------------

    risk_trends = []

    for employee in employees:
        trend = get_risk_trend(employee.employee_id, 30)

        risk_trends.append({
            "employee_id": employee.employee_id,
            "trend": trend["trend"]
        })

    # ---------------------------------------------
    # Compliance Metrics
    # ---------------------------------------------

    total_incidents = db.query(Incident).count()

    resolved_incidents = (
        db.query(Incident)
        .filter(Incident.status == "resolved")
        .count()
    )

    total_alerts = db.query(Alert).count()

    resolved_alerts = (
        db.query(Alert)
        .filter(Alert.status == "resolved")
        .count()
    )

    if total_incidents > 0:
        incident_resolution_rate = round(
            (resolved_incidents / total_incidents) * 100,
            1
        )
    else:
        incident_resolution_rate = 100.0

    if total_alerts > 0:
        alert_resolution_rate = round(
            (resolved_alerts / total_alerts) * 100,
            1
        )
    else:
        alert_resolution_rate = 100.0

    compliance_metrics = {
        "total_employees": total_employees,
        "total_incidents": total_incidents,
        "resolved_incidents": resolved_incidents,
        "incident_resolution_rate": incident_resolution_rate,
        "total_alerts": total_alerts,
        "resolved_alerts": resolved_alerts,
        "alert_resolution_rate": alert_resolution_rate
    }

    return {
        "organizational_risk_posture": {
            "risk_level": organizational_risk_posture,
            "average_risk_score": average_risk_score,
            "risk_distribution": risk_distribution
        },
        "risk_trends": risk_trends,
        "compliance_metrics": compliance_metrics
    }
