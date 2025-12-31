from uuid import UUID

from fastapi import APIRouter, Request, status, HTTPException, Depends

from services.auth.app.core.security import get_current_user_id, get_current_user
from services.auth.app.services.auth import AuthService
from services.auth.app.db.models import User
from services.auth.app.schemas.auth import (
    AuthResponse,
    UserLogin,
    UserRegister,
    TokenRefresh,
    TokenResponse,
    LogoutRequest,
    MessageResponse, UserResponse
)
from services.auth.app.services.auth import get_auth_service

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    return await auth_service.register(
        email=user_data.email,
        password=user_data.password,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    return await auth_service.login(
        email=credentials.email,
        password=credentials.password,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth_service.refresh_access_token(
        refresh_token=token_data.refresh_token,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    logout_data: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    success = await auth_service.logout(
        refresh_token=logout_data.refresh_token,
    )

    if success:
        return MessageResponse(message="Successfully logged out")
    else:
        return MessageResponse(message="Token not found or already invalidated")


@router.post("/logout-all", response_model=MessageResponse, dependencies=[Depends(get_current_user_id)])
async def logout_all(
    user_id: UUID = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    count = await auth_service.logout_all_sessions(user_id)

    return MessageResponse(
        message=f"Successfully logged out from {count} device(s)"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
