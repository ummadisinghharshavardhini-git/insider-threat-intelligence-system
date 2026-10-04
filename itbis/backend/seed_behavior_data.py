from datetime import datetime, timedelta
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["itbis"]
behavior_logs = db["behavior_logs"]

employee_id = "EMP001"

base_time = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)

sample_logs = []

for day in range(7):
    day_time = base_time - timedelta(days=day)

    sample_logs.extend([
        {
            "employee_id": employee_id,
            "activity": "login",
            "risk_score": 0,
            "device": "Laptop-01",
            "application": "Chrome",
            "data_volume": 0,
            "timestamp": day_time
        },
        {
            "employee_id": employee_id,
            "activity": "file_access",
            "risk_score": 0,
            "device": "Laptop-01",
            "application": "VS Code",
            "data_volume": 0,
            "timestamp": day_time + timedelta(minutes=30)
        },
        {
            "employee_id": employee_id,
            "activity": "app_usage",
            "risk_score": 0,
            "device": "Laptop-01",
            "application": "VS Code",
            "data_volume": 0,
            "timestamp": day_time + timedelta(minutes=45)
        },
        {
            "employee_id": employee_id,
            "activity": "file_upload",
            "risk_score": 0,
            "device": "Laptop-01",
            "application": "Chrome",
            "data_volume": 10,
            "timestamp": day_time + timedelta(hours=1)
        },
        {
            "employee_id": employee_id,
            "activity": "email_sent",
            "risk_score": 0,
            "device": "Laptop-01",
            "application": "Gmail",
            "data_volume": 0,
            "timestamp": day_time + timedelta(hours=2)
        }
    ])

behavior_logs.insert_many(sample_logs)

print(f"{len(sample_logs)} activity logs inserted successfully.")
