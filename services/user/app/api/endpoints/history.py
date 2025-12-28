from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user_id
from app.schemas.history import WatchHistoryResponse, WatchHistoryUpdate
from app.services.history import HistoryService, get_history_service
from app.services.user import UserService, get_user_service

router = APIRouter()


@router.get("/me/history", response_model=list[WatchHistoryResponse], tags=["History"])
async def get_watch_history(
    limit: int = Query(default=50, ge=1, le=100),
    user_id: UUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
    history_service: HistoryService = Depends(get_history_service),
):
    profile = await user_service.get_or_create_profile(user_id)

    history = await history_service.get_user_history(profile.id, limit=limit)

    return [WatchHistoryResponse.model_validate(h) for h in history]


@router.post("/me/history", response_model=WatchHistoryResponse, tags=["History"])
async def update_watch_progress(
    progress_data: WatchHistoryUpdate,
    user_id: UUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
    history_service: HistoryService = Depends(get_history_service),
):
    profile = await user_service.get_or_create_profile(user_id)

    history = await history_service.update_progress(profile.id, progress_data)

    return WatchHistoryResponse.model_validate(history)
