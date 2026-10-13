from datetime import datetime, timedelta, timezone

from pymongo import MongoClient

from app.models import Employee
from app.risk_scoring import calculate_risk_score


# ============================================================
# UEBA PEER COMPARISON
# ============================================================

def compare_to_peers(db, employee_id):

    employee = (
        db.query(Employee)
        .filter(Employee.employee_id == employee_id)
        .first()
    )

    if not employee:
        return {
            "error": "Employee not found"
        }

    peers = (
        db.query(Employee)
        .filter(
            Employee.department == employee.department,
            Employee.employee_id != employee_id
        )
        .all()
    )

    employee_risk = calculate_risk_score(employee_id)
    employee_score = employee_risk["risk_score"]

    if not peers:
        return {
            "employee_id": employee_id,
            "employee_score": employee_score,
            "department": employee.department,
            "peer_count": 0,
            "department_avg_score": None,
            "deviation_from_peers": None,
            "note": "No peers found in the same department"
        }

    peer_scores = []

    for peer in peers:
        peer_risk = calculate_risk_score(peer.employee_id)
        peer_scores.append(peer_risk["risk_score"])

    department_avg_score = sum(peer_scores) / len(peer_scores)

    deviation = employee_score - department_avg_score

    return {
        "employee_id": employee_id,
        "employee_score": employee_score,
        "department": employee.department,
        "peer_count": len(peers),
        "department_avg_score": round(department_avg_score, 1),
        "deviation_from_peers": round(deviation, 1)
    }


# ============================================================
# UEBA RISK TREND ANALYSIS
# ============================================================

def get_risk_trend(employee_id, days=30):

    client = MongoClient("mongodb://localhost:27017")
    db = client["itbis"]

    anomaly_logs = db["anomaly_logs"]

    start_date = (
        datetime.now(timezone.utc)
        - timedelta(days=days)
    )

    start_date_naive = start_date.replace(tzinfo=None)

    anomalies = list(
        anomaly_logs.find({
            "employee_id": employee_id,
            "anomaly": True,
            "detected_at": {
                "$gte": start_date_naive
            }
        })
    )

    daily_counts = {}

    for anomaly in anomalies:

        detected_at = anomaly.get("detected_at")

        if detected_at:

            date_key = detected_at.strftime("%Y-%m-%d")

            daily_counts[date_key] = (
                daily_counts.get(date_key, 0) + 1
            )

    trend = []

    for date in sorted(daily_counts.keys()):

        trend.append({
            "date": date,
            "anomaly_count": daily_counts[date]
        })

    client.close()

    return {
        "employee_id": employee_id,
        "days": days,
        "trend": trend
    }


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    from app.database import SessionLocal

    db = SessionLocal()

    try:

        # Peer comparison test
        peer_result = compare_to_peers(
            db,
            "EMP001"
        )

        print("\n===================================")
        print("UEBA PEER COMPARISON")
        print("===================================")
        print(peer_result)

        # Risk trend test
        trend_result = get_risk_trend(
            "EMP001",
            30
        )

        print("\n===================================")
        print("UEBA RISK TREND")
        print("===================================")
        print(trend_result)

    finally:
        db.close()
