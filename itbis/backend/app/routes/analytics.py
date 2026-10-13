from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Employee
from app.risk_scoring import calculate_risk_score


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/risk-distribution")
def get_risk_distribution(
    role: str,
    db: Session = Depends(get_db)
):
    if role not in ["admin", "security_manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only admin or security_manager can access risk distribution"
        )

    employees = db.query(Employee).all()

    distribution = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0
    }

    for employee in employees:
        risk = calculate_risk_score(employee.employee_id)
        category = risk["risk_category"]

        if category in distribution:
            distribution[category] += 1

    return {
        "total_employees": len(employees),
        "risk_distribution": distribution
    }
