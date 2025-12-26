# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.streaming_api_base import BaseStreamingApi
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
from pydantic import StrictStr
from typing import Any
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.progress_update_request import ProgressUpdateRequest
from openapi_server.models.progress_update_response import ProgressUpdateResponse
from openapi_server.models.stream_request import StreamRequest
from openapi_server.models.stream_response import StreamResponse
from openapi_server.models.watch_progress_response import WatchProgressResponse


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/api/v1/stream/{movie_id}",
    responses={
        200: {"model": StreamResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Streaming"],
    summary="Start Streaming",
    response_model_by_alias=True,
)
async def start_streaming_api_v1_stream_movie_id_post(
    movie_id: StrictStr = Path(..., description=""),
    authorization: StrictStr = Header(None, description=""),
    stream_request: StreamRequest = Body(None, description=""),
) -> StreamResponse:
    """Start streaming a movie  **Access Control:** - Requires valid JWT token - Requires active subscription  **Returns:** - Signed URL for HLS/DASH manifest - URL expires in 1 hour  **Example:** &#x60;&#x60;&#x60;bash curl -X POST http://localhost:8005/api/v1/stream/{movie_id} \\   -H \&quot;Authorization: Bearer &lt;token&gt;\&quot; \\   -H \&quot;Content-Type: application/json\&quot; \\   -d &#39;{\&quot;manifest_type\&quot;: \&quot;hls\&quot;}&#39; &#x60;&#x60;&#x60;"""
    if not BaseStreamingApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStreamingApi.subclasses[0]().start_streaming_api_v1_stream_movie_id_post(movie_id, authorization, stream_request)


@router.get(
    "/api/v1/stream/{movie_id}/progress",
    responses={
        200: {"model": WatchProgressResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Streaming"],
    summary="Get Watch Progress",
    response_model_by_alias=True,
)
async def get_watch_progress_api_v1_stream_movie_id_progress_get(
    movie_id: StrictStr = Path(..., description=""),
    authorization: StrictStr = Header(None, description=""),
) -> WatchProgressResponse:
    """Get current watch progress  **Returns:** - Current playback position - Last watched timestamp  **Example:** &#x60;&#x60;&#x60;bash curl http://localhost:8005/api/v1/stream/{movie_id}/progress \\   -H \&quot;Authorization: Bearer &lt;token&gt;\&quot; &#x60;&#x60;&#x60;"""
    if not BaseStreamingApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStreamingApi.subclasses[0]().get_watch_progress_api_v1_stream_movie_id_progress_get(movie_id, authorization)


@router.post(
    "/api/v1/stream/{movie_id}/progress",
    responses={
        200: {"model": ProgressUpdateResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Streaming"],
    summary="Update Watch Progress",
    response_model_by_alias=True,
)
async def update_watch_progress_api_v1_stream_movie_id_progress_post(
    movie_id: StrictStr = Path(..., description=""),
    authorization: StrictStr = Header(None, description=""),
    progress_update_request: ProgressUpdateRequest = Body(None, description=""),
) -> ProgressUpdateResponse:
    """Update watch progress  **Tracking:** - Saved to Redis (fast access) - Synced to PostgreSQL (persistent storage) - Kafka event published  **Client should call this endpoint periodically (e.g., every 10 seconds)**  **Example:** &#x60;&#x60;&#x60;bash curl -X POST http://localhost:8005/api/v1/stream/{movie_id}/progress \\   -H \&quot;Authorization: Bearer &lt;token&gt;\&quot; \\   -H \&quot;Content-Type: application/json\&quot; \\   -d &#39;{\&quot;position_seconds\&quot;: 120}&#39; &#x60;&#x60;&#x60;"""
    if not BaseStreamingApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStreamingApi.subclasses[0]().update_watch_progress_api_v1_stream_movie_id_progress_post(movie_id, authorization, progress_update_request)


@router.post(
    "/api/v1/stream/{movie_id}/stop",
    responses={
        200: {"model": object, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Streaming"],
    summary="Stop Streaming",
    response_model_by_alias=True,
)
async def stop_streaming_api_v1_stream_movie_id_stop_post(
    movie_id: StrictStr = Path(..., description=""),
    authorization: StrictStr = Header(None, description=""),
    progress_update_request: ProgressUpdateRequest = Body(None, description=""),
) -> object:
    """Stop streaming session  **Actions:** - Updates final watch progress - Publishes stream.stop event - Ends stream session  **Example:** &#x60;&#x60;&#x60;bash curl -X POST http://localhost:8005/api/v1/stream/{movie_id}/stop \\   -H \&quot;Authorization: Bearer &lt;token&gt;\&quot; \\   -H \&quot;Content-Type: application/json\&quot; \\   -d &#39;{\&quot;position_seconds\&quot;: 1800}&#39; &#x60;&#x60;&#x60;"""
    if not BaseStreamingApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStreamingApi.subclasses[0]().stop_streaming_api_v1_stream_movie_id_stop_post(movie_id, authorization, progress_update_request)
