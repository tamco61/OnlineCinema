import logging
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.clickhouse import get_clickhouse_client, ClickHouseClient
from app.services.analytics import AnalyticsService
from app.schemas.analytics import (
    PopularContentResponse,
    UserStatsResponse,
    ViewingEventCreate
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(
    ch_client: ClickHouseClient = Depends(get_clickhouse_client)
) -> AnalyticsService:
    return AnalyticsService(ch_client)


@router.get("/content/popular", response_model=PopularContentResponse)
async def get_popular_content(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    try:
        return analytics_service.get_popular_content(days=days, limit=limit)

    except Exception as e:
        logger.error(f"Error getting popular content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get popular content")


@router.get("/user/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    try:
        return analytics_service.get_user_stats(user_id=user_id, days=days)

    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user statistics")


@router.get("/trends")
async def get_viewing_trends(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    try:
        return analytics_service.get_viewing_trends(days=days)

    except Exception as e:
        logger.error(f"Error getting viewing trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get viewing trends")


@router.get("/peak-hours")
async def get_peak_hours(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    try:
        return analytics_service.get_peak_hours(days=days)

    except Exception as e:
        logger.error(f"Error getting peak hours: {e}")
        raise HTTPException(status_code=500, detail="Failed to get peak hours")


@router.post("/events")
async def create_viewing_event(
    event: ViewingEventCreate,
    ch_client: ClickHouseClient = Depends(get_clickhouse_client)
):

    try:
        ch_client.insert_viewing_event(
            user_id=event.user_id,
            movie_id=event.movie_id,
            event_type=event.event_type,
            position_seconds=event.position_seconds,
            event_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            session_id=event.session_id,
            metadata=json.dumps(event.metadata)
        )

        return {
            "success": True,
            "message": "Viewing event created"
        }

    except Exception as e:
        logger.error(f"Error creating viewing event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create viewing event")
