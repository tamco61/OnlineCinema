from uuid import UUID

from fastapi import APIRouter, Depends

from services.user.app.core.security import get_current_user_id
from services.user.app.schemas.user import UserProfileResponse, UserProfileUpdate
from services.user.app.services.user import UserService, get_user_service

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse, tags=["Users"])
async def get_my_profile(
        user_id: UUID = Depends(get_current_user_id),
        user_service: UserService = Depends(get_user_service),
):
    profile = await user_service.get_or_create_profile(user_id)
    return UserProfileResponse.model_validate(profile)


@router.patch("/me", response_model=UserProfileResponse, tags=["Users"])
async def update_my_profile(
        profile_data: UserProfileUpdate,
        user_id: UUID = Depends(get_current_user_id),
        user_service: UserService = Depends(get_user_service),
):
    profile = await user_service.update_profile(user_id, profile_data)
    return UserProfileResponse.model_validate(profile)
