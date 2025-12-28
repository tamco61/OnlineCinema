from fastapi import APIRouter, Request, status, HTTPException, Depends
from uuid import UUID


from app.core.security import get_current_user_id, get_current_user
from app.services.auth import AuthService
from app.db.models import User
from app.schemas.auth import (
    AuthResponse,
    UserLogin,
    UserRegister,
    TokenRefresh,
    TokenResponse,
    LogoutRequest,
    MessageResponse, UserResponse
)

from app.services.auth import get_auth_service

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends()
) -> AuthResponse:
    # todo
    pass


@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    # todo
    pass


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    # todo
    pass


@router.post("/logout", response_model=MessageResponse)
async def logout(
    logout_data: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    # todo
    pass


@router.post("/logout-all", response_model=MessageResponse, dependencies=[Depends(get_current_user_id)])
async def logout_all(
    user_id: UUID = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    # todo
    pass


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    # todo
    pass