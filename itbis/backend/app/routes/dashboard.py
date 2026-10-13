
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Employee, Incident, Alert, AuditLog
from app.risk_scoring import calculate_risk_score
from app.ueba import get_risk_trend


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# ============================================================
# ANALYST DASHBOARD
# ============================================================


@router.get("/analyst")
def analyst_dashboard(
    role: str,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "security_analyst"]:
        raise HTTPException(status_code=403, detail="Access denied")

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


# ============================================================
# SOC DASHBOARD
# ============================================================

@router.get("/soc")
def soc_dashboard(
    role: str,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "security_analyst"]:
        raise HTTPException(status_code=403, detail="Access denied")

    from pymongo import MongoClient

    client = MongoClient(
        "mongodb://localhost:27017",
        serverSelectionTimeoutMS=3000
    )

    try:
        mongo_db = client["itbis"]

        behavior_logs = mongo_db["behavior_logs"]
        anomaly_logs = mongo_db["anomaly_logs"]

        security_events_count = behavior_logs.count_documents({})
        behavioral_anomalies_count = anomaly_logs.count_documents({
            "anomaly": True
        })
    finally:
        client.close()

    active_investigations = (
        db.query(Incident)
        .filter(Incident.status.in_(["open", "investigating"]))
        .count()
    )

    recent_alerts = (
        db.query(Alert)
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )

    recent_threat_intelligence_notes = [
        {
            "alert_id": alert.id,
            "employee_id": alert.employee_id,
            "severity": alert.severity,
            "message": alert.message,
            "status": alert.status,
            "created_at": alert.created_at
        }
        for alert in recent_alerts
    ]

    return {
        "security_events_count": security_events_count,
        "behavioral_anomalies_count": behavioral_anomalies_count,
        "active_investigations": active_investigations,
        "recent_threat_intelligence_notes":
            recent_threat_intelligence_notes
    }


# ============================================================
# SECURITY MANAGER DASHBOARD
# ============================================================

@router.get("/security-manager")
def security_manager_dashboard(
    role: str,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "security_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")

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

    average_risk_score = (
        round(total_risk_score / total_employees, 1)
        if total_employees > 0
        else 0.0
    )

    if risk_distribution["critical"] > 0:
        organizational_risk_posture = "critical"
    elif risk_distribution["high"] > 0:
        organizational_risk_posture = "high"
    elif risk_distribution["medium"] > 0:
        organizational_risk_posture = "medium"
    else:
        organizational_risk_posture = "low"

    risk_trends = []

    for employee in employees:
        trend_data = get_risk_trend(employee.employee_id, 30)

        risk_trends.append({
            "employee_id": employee.employee_id,
            "trend": trend_data["trend"]
        })

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

    incident_resolution_rate = (
        round(resolved_incidents / total_incidents * 100, 1)
        if total_incidents > 0
        else 100.0
    )

    alert_resolution_rate = (
        round(resolved_alerts / total_alerts * 100, 1)
        if total_alerts > 0
        else 100.0
    )

    compliance_metrics = {
        "total_employees": total_employees,
        "risk_distribution": risk_distribution,
        "average_risk_score": average_risk_score,
        "total_incidents": total_incidents,
        "resolved_incidents": resolved_incidents,
        "incident_resolution_rate": incident_resolution_rate,
        "total_alerts": total_alerts,
        "resolved_alerts": resolved_alerts,
        "alert_resolution_rate": alert_resolution_rate
    }

    return {
        "organizational_risk_posture": organizational_risk_posture,
        "risk_distribution": risk_distribution,
        "average_risk_score": average_risk_score,
        "risk_trends": risk_trends,
        "compliance_metrics": compliance_metrics
    }


# ============================================================
# DAY 32: ADMIN DASHBOARD
# ============================================================

@router.get("/admin")
def admin_dashboard(
    role: str,
    db: Session = Depends(get_db)
):
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can access this dashboard"
        )

    total_platform_users = db.query(User).count()
    employees_monitored = db.query(Employee).count()
    total_incidents = db.query(Incident).count()

    open_incidents = (
        db.query(Incident)
        .filter(Incident.status == "open")
        .count()
    )

    role_breakdown = {
        "employee": 0,
        "security_analyst": 0,
        "soc_engineer": 0,
        "security_manager": 0,
        "admin": 0
    }

    users = db.query(User.role).all()

    for user in users:
        user_role = user[0]

        if user_role:
            role_breakdown[user_role] = (
                role_breakdown.get(user_role, 0) + 1
            )

    departments = (
        db.query(Employee.department)
        .filter(
            Employee.department.isnot(None),
            Employee.department != ""
        )
        .distinct()
        .all()
    )

    distinct_departments = len(departments)

    return {
        "total_platform_users": total_platform_users,
        "users_by_role": role_breakdown,
        "employees_monitored": employees_monitored,
        "distinct_departments": distinct_departments,

        # Preserve existing response fields
        "user_count": total_platform_users,
        "employee_count": employees_monitored,
        "total_incidents": total_incidents,
        "open_incidents": open_incidents
    }


# ============================================================
# DAY 32: ADMIN PLATFORM ANALYTICS
# ============================================================


@router.get("/admin/platform-analytics")
def admin_platform_analytics(role: str):
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can access platform analytics"
        )

    from pymongo import MongoClient

    client = MongoClient(
        "mongodb://localhost:27017",
        serverSelectionTimeoutMS=3000
    )

    try:
        mongo_db = client["itbis"]

        # Total activity/behavior records
        total_activity_logs = mongo_db[
            "behavior_logs"
        ].count_documents({})

        # Rule-based anomalies from the actual collections
        numeric_anomalies = mongo_db[
            "numeric_anomalies"
        ].count_documents({"anomaly": True})

        rule_anomalies = mongo_db[
            "anomaly_logs"
        ].count_documents({"anomaly": True})

        # ML anomaly records use ml_prediction in this project.
        # Inspect the field values before treating them as anomalies.
        ml_collection = mongo_db["ml_anomaly_logs"]
        ml_anomalies = ml_collection.count_documents({
            "ml_prediction": -1
        })

        # Combined anomaly records
        combined_anomalies = mongo_db[
            "combined_anomaly_logs"
        ].count_documents({"anomaly": True})

        # Avoid double-counting the same events across collections:
        # report each collection separately and use the combined
        # collection for the overall anomaly count.
        total_anomalies = combined_anomalies

        overall_anomaly_rate_percent = (
            round(
                total_anomalies / total_activity_logs * 100,
                2
            )
            if total_activity_logs > 0
            else 0.0
        )

        return {
            "total_activity_logs": total_activity_logs,
            "numeric_anomalies": numeric_anomalies,
            "rule_anomalies": rule_anomalies,
            "ml_anomalies": ml_anomalies,
            "combined_anomalies": combined_anomalies,
            "total_anomalies": total_anomalies,
            "overall_anomaly_rate_percent":
                overall_anomaly_rate_percent
        }

    finally:
        client.close()

# ============================================================
# DAY 31: MANAGER COMPLIANCE
# ============================================================


@router.get("/manager/compliance")
def manager_compliance(
    role: str,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "security_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")

    total_incidents = db.query(Incident).count()

    resolved_incidents = (
        db.query(Incident)
        .filter(Incident.status.in_(["resolved", "closed"]))
        .count()
    )

    resolution_rate = (
        round(resolved_incidents / total_incidents * 100, 1)
        if total_incidents > 0
        else 0.0
    )

    open_critical_incidents = (
        db.query(Incident)
        .filter(
            Incident.status == "open",
            Incident.severity.ilike("critical")
        )
        .count()
    )

    return {
        "total_incidents": total_incidents,
        "resolved_incidents": resolved_incidents,
        "resolution_rate_percent": resolution_rate,
        "open_critical_incidents": open_critical_incidents
    }


# ============================================================
# DAY 31: MEAN TIME TO RESOLVE (MTTR)
# ============================================================

def calculate_mttr(db: Session):
    resolved_alerts = (
        db.query(Alert)
        .filter(
            Alert.status == "resolved",
            Alert.resolved_at.isnot(None),
            Alert.created_at.isnot(None)
        )
        .all()
    )

    if not resolved_alerts:
        return None

    valid_alerts = [
        alert for alert in resolved_alerts
        if alert.resolved_at >= alert.created_at
    ]

    if not valid_alerts:
        return None

    total_hours = sum(
        (
            alert.resolved_at - alert.created_at
        ).total_seconds() / 3600
        for alert in valid_alerts
    )

    return round(total_hours / len(valid_alerts), 2)


# ============================================================
# DAY 31: MEAN TIME TO INVESTIGATE (MTTI)
# ============================================================

def calculate_mtti(db: Session):
    incidents = (
        db.query(Incident)
        .filter(
            Incident.created_at.isnot(None),
            Incident.investigation_started_at.isnot(None)
        )
        .all()
    )

    if not incidents:
        return None

    valid_incidents = [
        incident for incident in incidents
        if incident.investigation_started_at >= incident.created_at
    ]

    if not valid_incidents:
        return None

    total_hours = sum(
        (
            incident.investigation_started_at
            - incident.created_at
        ).total_seconds() / 3600
        for incident in valid_incidents
    )

    return round(total_hours / len(valid_incidents), 2)


# ============================================================
# DAY 31: MANAGER RESPONSE METRICS
# ============================================================

@router.get("/manager/response-metrics")
def manager_response_metrics(
    role: str,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "security_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "mttr_hours": calculate_mttr(db),
        "mtti_hours": calculate_mtti(db),
        "mtti_is_approximation": False,
        "mttr_note": (
            "MTTR is calculated using alert creation and resolution timestamps."
        ),
        "mtti_note": (
            "MTTI is calculated using incident creation and investigation start timestamps."
        )
    }

# ============================================================
# ADMIN AUDIT LOG
# ============================================================


@router.get("/admin/audit-log")
def get_admin_audit_log(
    role: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can access audit logs"
        )

    if limit < 1 or limit > 200:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 200"
        )

    audit_logs = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "details": log.details,
            "timestamp": log.timestamp
        }
        for log in audit_logs
    ]
