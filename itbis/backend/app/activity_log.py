from datetime import datetime
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["itbis"]

behavior_logs = db["behavior_logs"]


def log_activity(employee_id, activity, risk_score=0):
    log = {
        "employee_id": employee_id,
        "activity": activity,
        "risk_score": risk_score,
        "timestamp": datetime.utcnow()
    }

    behavior_logs.insert_one(log)
