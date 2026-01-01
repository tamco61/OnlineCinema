from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from services.user.app.core.security import get_current_user_id
from services.user.app.schemas.favorites import FavoriteResponse
from services.user.app.services.favorites import FavoritesService, get_favorites_service
from services.user.app.services.user import UserService, get_user_service

router = APIRouter()


@router.get("/me/favorites", response_model=list[FavoriteResponse], tags=["Favorites"])
async def get_favorites(
        limit: int = Query(default=100, ge=1, le=500),
        user_id: UUID = Depends(get_current_user_id),
        user_service: UserService = Depends(get_user_service),
        favorites_service: FavoritesService = Depends(get_favorites_service),
):
    profile = await user_service.get_or_create_profile(user_id)

    favorites = await favorites_service.get_user_favorites(profile.id, limit=limit)

    return [FavoriteResponse.model_validate(f) for f in favorites]


@router.post("/me/favorites/{content_id}", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED,
             tags=["Favorites"])
async def add_to_favorites(
        content_id: UUID,
        content_type: str = Query(..., description="Content type: movie, series, etc."),
        user_id: UUID = Depends(get_current_user_id),
        user_service: UserService = Depends(get_user_service),
        favorites_service: FavoritesService = Depends(get_favorites_service),
):
    profile = await user_service.get_or_create_profile(user_id)

    favorite = await favorites_service.add_favorite(
        profile.id, content_id, content_type
    )

    return FavoriteResponse.model_validate(favorite)


@router.delete("/me/favorites/{content_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Favorites"])
async def remove_from_favorites(
        content_id: UUID,
        user_id: UUID = Depends(get_current_user_id),
        user_service: UserService = Depends(get_user_service),
        favorites_service: FavoritesService = Depends(get_favorites_service),
):
    profile = await user_service.get_or_create_profile(user_id)

    await favorites_service.remove_favorite(profile.id, content_id)

    return None
