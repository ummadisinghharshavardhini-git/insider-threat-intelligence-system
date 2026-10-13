from fastapi import APIRouter
from pymongo import MongoClient


router = APIRouter(
    prefix="/risk",
    tags=["Risk"]
)


# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["itbis"]
risk_scores = db["risk_scores"]


@router.get("/{employee_id}")
def get_employee_risk(employee_id: str):
    result = risk_scores.find_one(
        {"employee_id": employee_id},
        {"_id": 0}
    )

    if not result:
        return {
            "employee_id": employee_id,
            "message": "No risk score found"
        }

    return result
