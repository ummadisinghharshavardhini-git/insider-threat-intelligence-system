from fastapi import APIRouter, Query
from pymongo import MongoClient


router = APIRouter(
    prefix="/anomalies",
    tags=["Anomalies"]
)


# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["itbis"]
anomaly_logs = db["anomaly_logs"]


@router.get("/")
def get_anomalies(
    limit: int = Query(50, ge=1, le=200)
):
    anomalies = list(
        anomaly_logs.find(
            {},
            {"_id": 0}
        )
        .sort("timestamp", -1)
        .limit(limit)
    )

    return anomalies
