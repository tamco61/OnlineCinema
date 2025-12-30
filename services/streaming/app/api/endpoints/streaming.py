import logging

from fastapi import APIRouter, Depends, HTTPException, Header, Request

from app.core.security import verify_access_token
from app.core.config import settings
from app.services.streaming import StreamingService, get_streaming_service
from app.schemas.streaming import (
    StreamRequest,
    StreamResponse,
    ProgressUpdateRequest,
    ProgressUpdateResponse,
    WatchProgressResponse
)


logger = logging.getLogger(__name__)

router = APIRouter()


def get_access_token(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    return authorization.replace("Bearer ", "")


async def get_current_user_id(access_token: str = Depends(get_access_token)) -> str:
    user_id = verify_access_token(access_token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return str(user_id)


@router.post("/{movie_id}", response_model=StreamResponse)
async def start_streaming(
    movie_id: str,
    request_body: StreamRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    access_token: str = Depends(get_access_token),
    streaming_service: StreamingService = Depends(get_streaming_service)
):
    has_access, reason = await streaming_service.check_access(user_id, access_token)

    if not has_access:
        raise HTTPException(status_code=403, detail=f"Access denied: {reason}")

    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    try:
        manifest_url = await streaming_service.start_stream(
            user_id=user_id,
            movie_id=movie_id,
            manifest_type=request_body.manifest_type,
            user_agent=user_agent,
            ip_address=ip_address
        )

        return StreamResponse(
            manifest_url=manifest_url,
            expires_in=settings.SIGNED_URL_EXPIRATION,
            manifest_type=request_body.manifest_type
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting stream: {e}")
        raise HTTPException(status_code=500, detail="Failed to start streaming")


@router.post("/{movie_id}/progress", response_model=ProgressUpdateResponse)
async def update_watch_progress(
    movie_id: str,
    progress: ProgressUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    streaming_service: StreamingService = Depends(get_streaming_service)
):
    try:
        await streaming_service.update_progress(
            user_id=user_id,
            movie_id=movie_id,
            position_seconds=progress.position_seconds
        )

        return ProgressUpdateResponse(
            success=True,
            position_seconds=progress.position_seconds
        )

    except Exception as e:
        logger.error(f"Error updating progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to update progress")


@router.get("/{movie_id}/progress", response_model=WatchProgressResponse)
async def get_watch_progress(
    movie_id: str,
    user_id: str = Depends(get_current_user_id),
    streaming_service: StreamingService = Depends(get_streaming_service)
):
    try:
        position = await streaming_service.get_progress(user_id, movie_id)

        return WatchProgressResponse(
            user_id=user_id,
            movie_id=movie_id,
            position_seconds=position
        )

    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get progress")


@router.post("/{movie_id}/stop")
async def stop_streaming(
    movie_id: str,
    progress: ProgressUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    streaming_service: StreamingService = Depends(get_streaming_service)
):
    try:
        await streaming_service.end_stream(
            user_id=user_id,
            movie_id=movie_id,
            position_seconds=progress.position_seconds
        )

        return {
            "success": True,
            "message": "Stream stopped successfully"
        }

    except Exception as e:
        logger.error(f"Error stopping stream: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop stream")
