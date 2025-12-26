# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.analytics_api_base import BaseAnalyticsApi
import openapi_server.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from openapi_server.models.extra_models import TokenModel  # noqa: F401
from pydantic import Field, StrictStr
from typing import Any, Optional
from typing_extensions import Annotated
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.popular_content_response import PopularContentResponse
from openapi_server.models.user_stats_response import UserStatsResponse
from openapi_server.models.viewing_event_create import ViewingEventCreate


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/v1/analytics/content/popular",
    responses={
        200: {"model": PopularContentResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Analytics"],
    summary="Get Popular Content",
    response_model_by_alias=True,
)
async def get_popular_content_api_v1_analytics_content_popular_get(
    days: Annotated[Optional[Annotated[int, Field(le=365, strict=True, ge=1)]], Field(description="Number of days to analyze")] = Query(7, description="Number of days to analyze", alias="days", ge=1, le=365),
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of results")] = Query(10, description="Maximum number of results", alias="limit", ge=1, le=100),
) -> PopularContentResponse:
    """Get most popular movies by views  **Query ClickHouse:** &#x60;&#x60;&#x60;sql SELECT     movie_id,     sum(start_count) as total_views,     sum(unique_viewers) as unique_viewers,     round(sum(finish_count) / sum(start_count) * 100, 2) as completion_rate FROM popular_content_mv WHERE event_date &gt;&#x3D; today() - 7 GROUP BY movie_id ORDER BY total_views DESC LIMIT 10 &#x60;&#x60;&#x60;  **Example:** &#x60;&#x60;&#x60;bash curl \&quot;http://localhost:8006/api/v1/analytics/content/popular?days&#x3D;7&amp;limit&#x3D;10\&quot; &#x60;&#x60;&#x60;  **Response:** &#x60;&#x60;&#x60;json {   \&quot;items\&quot;: [     {       \&quot;movie_id\&quot;: \&quot;uuid\&quot;,       \&quot;total_views\&quot;: 1500,       \&quot;unique_viewers\&quot;: 800,       \&quot;completion_rate\&quot;: 75.5     }   ],   \&quot;period_days\&quot;: 7,   \&quot;total_items\&quot;: 10 } &#x60;&#x60;&#x60;"""
    if not BaseAnalyticsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAnalyticsApi.subclasses[0]().get_popular_content_api_v1_analytics_content_popular_get(days, limit)


@router.get(
    "/api/v1/analytics/user/{user_id}/stats",
    responses={
        200: {"model": UserStatsResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Analytics"],
    summary="Get User Stats",
    response_model_by_alias=True,
)
async def get_user_stats_api_v1_analytics_user_user_id_stats_get(
    user_id: StrictStr = Path(..., description=""),
    days: Annotated[Optional[Annotated[int, Field(le=365, strict=True, ge=1)]], Field(description="Number of days to analyze")] = Query(30, description="Number of days to analyze", alias="days", ge=1, le=365),
) -> UserStatsResponse:
    """Get user viewing statistics  **Queries ClickHouse:**  1. **Main stats:** &#x60;&#x60;&#x60;sql SELECT     sum(movies_started) as total_started,     sum(movies_finished) as total_finished,     sum(unique_movies) as unique_movies FROM user_stats_mv WHERE user_id &#x3D; &#39;{user_id}&#39;   AND event_date &gt;&#x3D; today() - 30 &#x60;&#x60;&#x60;  2. **Total watch time:** &#x60;&#x60;&#x60;sql SELECT sum(position_seconds) as total_seconds FROM viewing_events WHERE user_id &#x3D; &#39;{user_id}&#39;   AND event_type &#x3D; &#39;finish&#39;   AND event_time &gt;&#x3D; now() - INTERVAL 30 DAY &#x60;&#x60;&#x60;  3. **Most watched movie:** &#x60;&#x60;&#x60;sql SELECT movie_id, count() as watch_count FROM viewing_events WHERE user_id &#x3D; &#39;{user_id}&#39;   AND event_type &#x3D; &#39;start&#39;   AND event_time &gt;&#x3D; now() - INTERVAL 30 DAY GROUP BY movie_id ORDER BY watch_count DESC LIMIT 1 &#x60;&#x60;&#x60;  **Example:** &#x60;&#x60;&#x60;bash curl \&quot;http://localhost:8006/api/v1/analytics/user/{user_id}/stats?days&#x3D;30\&quot; &#x60;&#x60;&#x60;  **Response:** &#x60;&#x60;&#x60;json {   \&quot;user_id\&quot;: \&quot;uuid\&quot;,   \&quot;movies_started\&quot;: 25,   \&quot;movies_finished\&quot;: 18,   \&quot;unique_movies_watched\&quot;: 20,   \&quot;total_watch_time_seconds\&quot;: 108000,   \&quot;completion_rate\&quot;: 72.0,   \&quot;period_days\&quot;: 30,   \&quot;most_watched_movie_id\&quot;: \&quot;uuid\&quot; } &#x60;&#x60;&#x60;"""
    if not BaseAnalyticsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAnalyticsApi.subclasses[0]().get_user_stats_api_v1_analytics_user_user_id_stats_get(user_id, days)


@router.get(
    "/api/v1/analytics/trends",
    responses={
        200: {"model": object, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Analytics"],
    summary="Get Viewing Trends",
    response_model_by_alias=True,
)
async def get_viewing_trends_api_v1_analytics_trends_get(
    days: Annotated[Optional[Annotated[int, Field(le=90, strict=True, ge=1)]], Field(description="Number of days to analyze")] = Query(7, description="Number of days to analyze", alias="days", ge=1, le=90),
) -> object:
    """Get viewing trends over time  **Query ClickHouse:** &#x60;&#x60;&#x60;sql SELECT     toDate(event_time) as date,     countIf(event_type &#x3D; &#39;start&#39;) as starts,     countIf(event_type &#x3D; &#39;finish&#39;) as finishes,     uniq(user_id) as unique_users,     uniq(movie_id) as unique_movies FROM viewing_events WHERE event_time &gt;&#x3D; now() - INTERVAL 7 DAY GROUP BY date ORDER BY date &#x60;&#x60;&#x60;  **Example:** &#x60;&#x60;&#x60;bash curl \&quot;http://localhost:8006/api/v1/analytics/trends?days&#x3D;7\&quot; &#x60;&#x60;&#x60;  **Response:** &#x60;&#x60;&#x60;json {   \&quot;period_days\&quot;: 7,   \&quot;trends\&quot;: [     {       \&quot;date\&quot;: \&quot;2024-11-10\&quot;,       \&quot;starts\&quot;: 500,       \&quot;finishes\&quot;: 350,       \&quot;unique_users\&quot;: 200,       \&quot;unique_movies\&quot;: 50     }   ] } &#x60;&#x60;&#x60;"""
    if not BaseAnalyticsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAnalyticsApi.subclasses[0]().get_viewing_trends_api_v1_analytics_trends_get(days)


@router.get(
    "/api/v1/analytics/peak-hours",
    responses={
        200: {"model": object, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Analytics"],
    summary="Get Peak Hours",
    response_model_by_alias=True,
)
async def get_peak_hours_api_v1_analytics_peak_hours_get(
    days: Annotated[Optional[Annotated[int, Field(le=90, strict=True, ge=1)]], Field(description="Number of days to analyze")] = Query(7, description="Number of days to analyze", alias="days", ge=1, le=90),
) -> object:
    """Get peak viewing hours  **Query ClickHouse:** &#x60;&#x60;&#x60;sql SELECT     toHour(event_time) as hour,     count() as events_count,     uniq(user_id) as unique_users FROM viewing_events WHERE event_time &gt;&#x3D; now() - INTERVAL 7 DAY GROUP BY hour ORDER BY hour &#x60;&#x60;&#x60;  **Example:** &#x60;&#x60;&#x60;bash curl \&quot;http://localhost:8006/api/v1/analytics/peak-hours?days&#x3D;7\&quot; &#x60;&#x60;&#x60;  **Response:** &#x60;&#x60;&#x60;json {   \&quot;period_days\&quot;: 7,   \&quot;peak_hours\&quot;: [     {       \&quot;hour\&quot;: 20,       \&quot;events_count\&quot;: 5000,       \&quot;unique_users\&quot;: 1200     }   ] } &#x60;&#x60;&#x60;"""
    if not BaseAnalyticsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAnalyticsApi.subclasses[0]().get_peak_hours_api_v1_analytics_peak_hours_get(days)


@router.post(
    "/api/v1/analytics/events",
    responses={
        200: {"model": object, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Analytics"],
    summary="Create Viewing Event",
    response_model_by_alias=True,
)
async def create_viewing_event_api_v1_analytics_events_post(
    viewing_event_create: ViewingEventCreate = Body(None, description=""),
) -> object:
    """Create viewing event manually (HTTP endpoint)  **Note:** This is optional. Events are typically consumed from Kafka.  **Body:** &#x60;&#x60;&#x60;json {   \&quot;user_id\&quot;: \&quot;uuid\&quot;,   \&quot;movie_id\&quot;: \&quot;uuid\&quot;,   \&quot;event_type\&quot;: \&quot;start\&quot;,   \&quot;position_seconds\&quot;: 0,   \&quot;session_id\&quot;: \&quot;uuid\&quot;,   \&quot;metadata\&quot;: {} } &#x60;&#x60;&#x60;  **Example:** &#x60;&#x60;&#x60;bash curl -X POST http://localhost:8006/api/v1/analytics/events \\   -H \&quot;Content-Type: application/json\&quot; \\   -d &#39;{     \&quot;user_id\&quot;: \&quot;uuid\&quot;,     \&quot;movie_id\&quot;: \&quot;uuid\&quot;,     \&quot;event_type\&quot;: \&quot;start\&quot;,     \&quot;position_seconds\&quot;: 0   }&#39; &#x60;&#x60;&#x60;"""
    if not BaseAnalyticsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAnalyticsApi.subclasses[0]().create_viewing_event_api_v1_analytics_events_post(viewing_event_create)
