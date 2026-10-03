from fastapi import APIRouter, Query
from ..activity_log import behavior_logs

router = APIRouter(
    prefix="/activity",
    tags=["Activity"]
)


@router.get("/")
def get_activities(
    limit: int = Query(50, ge=1, le=200)
):
    logs = list(
        behavior_logs.find(
            {},
            {"_id": 0}
        )
        .sort("timestamp", -1)
        .limit(limit)
    )

    return logs
