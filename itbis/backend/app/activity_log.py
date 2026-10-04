from datetime import datetime
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["itbis"]

behavior_logs = db["behavior_logs"]


def log_activity(
    employee_id,
    activity,
    risk_score=0,
    device=None,
    application=None,
    data_volume=0
):
    log = {
        "employee_id": employee_id,
        "activity": activity,
        "risk_score": risk_score,
        "device": device,
        "application": application,
        "data_volume": data_volume,
        "timestamp": datetime.utcnow()
    }

    behavior_logs.insert_one(log)

    return log
