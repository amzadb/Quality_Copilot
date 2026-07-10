from fastapi import APIRouter, Depends, Query

from app.schemas.activity import ActivityItem, ActivitySummary
from app.services.activity_service import ActivityService, get_activity_service

router = APIRouter()


@router.get("/recent", response_model=list[ActivityItem])
async def get_recent_activity(
    limit: int = Query(default=20, ge=1, le=100),
    service: ActivityService = Depends(get_activity_service),
) -> list[ActivityItem]:
    return await service.get_recent(limit=limit)


@router.get("/summary", response_model=ActivitySummary)
async def get_activity_summary(
    service: ActivityService = Depends(get_activity_service),
) -> ActivitySummary:
    return await service.get_summary()
