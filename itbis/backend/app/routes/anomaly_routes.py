from fastapi import APIRouter
from pymongo import MongoClient

router = APIRouter(
    prefix="/anomalies",
    tags=["Combined Anomalies"]
)

client = MongoClient("mongodb://localhost:27017")
db = client["itbis"]

anomaly_logs = db["anomaly_logs"]
ml_anomaly_logs = db["ml_anomaly_logs"]


# SUMMARY ROUTE MUST COME FIRST
@router.get("/summary")
def get_anomaly_summary():

    pipeline = [
        {
            "$match": {
                "anomaly": True
            }
        },
        {
            "$group": {
                "_id": "$employee_id",
                "total_anomalies": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "total_anomalies": -1
            }
        },
        {
            "$limit": 10
        }
    ]

    summary = list(
        anomaly_logs.aggregate(pipeline)
    )

    result = []

    for item in summary:
        result.append({
            "employee_id": item["_id"],
            "total_anomalies": item["total_anomalies"]
        })

    return {
        "summary": result
    }


# EMPLOYEE ROUTE AFTER SUMMARY
@router.get("/{employee_id}")
def get_anomaly_report(employee_id: str):

    rule_based = list(
        anomaly_logs.find(
            {
                "employee_id": employee_id,
                "anomaly": True
            },
            {"_id": 0}
        )
    )

    ml_based = list(
        ml_anomaly_logs.find(
            {
                "employee_id": employee_id,
                "ml_prediction": -1
            },
            {"_id": 0}
        )
    )

    rule_based.sort(
        key=lambda x: x.get("detected_at")
    )

    ml_based.sort(
        key=lambda x: x.get("date")
    )

    return {
        "employee_id": employee_id,
        "total_flags": len(rule_based) + len(ml_based),
        "rule_based_anomalies": rule_based,
        "ml_flagged_days": ml_based
    }
