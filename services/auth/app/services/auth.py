from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional

from app.db.session import get_db # noqa
from app.db.models import User # noqa
from app.schemas.auth import AuthResponse, TokenPair, UserResponse, TokenResponse # noqa
from app.core.security import get_password_hash, verify_password # noqa

from app.services.jwt import JWTService, get_jwt_service
from app.services.redis import RedisService, get_redis_service


class AuthService:
    def __init__(self, db: AsyncSession, jwt_service: JWTService, redis_service: RedisService):
        self.db = db
        self.jwt_service = jwt_service
        self.redis_service = redis_service

    async def _create_tokens_for_user(self, user_id: UUID) -> TokenPair:
        access_token, access_expires_in = self.jwt_service.create_access_token(user_id)
        refresh_token, token_id, refresh_expires_in = self.jwt_service.create_refresh_token(user_id)

        await self.redis_service.store_refresh_token(
            user_id=user_id,
            token_id=token_id,
            token_value=refresh_token,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=access_expires_in,
        )

    async def register(self, email: str, password: str) -> AuthResponse:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )

        exist_user = result.scalar_one_or_none()

        if exist_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="email already registered"
            )

        password_hash = get_password_hash(password)

        new_user = User(
            email=email,
            password_hash=password_hash,
            is_active=True
        )

        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
        except Exception:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="add user db error"
            )

        tokens = await self._create_tokens_for_user(new_user.id)

        user_response = UserResponse.model_validate(new_user)
        return AuthResponse(user=user_response, tokens=tokens)

    async def login(self, email: str, password: str) -> AuthResponse:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        tokens = await self._create_tokens_for_user(user.id)
        user_response = UserResponse.model_validate(user)

        return AuthResponse(user=user_response, tokens=tokens)

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        token_data = self.jwt_service.verify_refresh_token(refresh_token)

        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id, token_id = token_data

        is_valid = await self.redis_service.verify_refresh_token(
            user_id=user_id,
            token_id=token_id,
            token_value=refresh_token,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        access_token, expires_in = self.jwt_service.create_access_token(user_id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        )

    async def logout(self, refresh_token: str) -> bool:
        token_data = self.jwt_service.verify_refresh_token(refresh_token)

        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id, token_id = token_data

        deleted = await self.redis_service.delete_refresh_token(
            user_id=user_id,
            token_id=token_id,
        )

        return deleted

    async def logout_all_sessions(self, user_id: UUID) -> int:
        count = await self.redis_service.delete_all_user_tokens(user_id)
        return count

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


async def get_auth_service(
        db: AsyncSession = Depends(get_db),
        jwt_service: JWTService = Depends(get_jwt_service),
        redis_service: RedisService = Depends(get_redis_service)
) -> AuthService:
    return AuthService(db=db, jwt_service=jwt_service, redis_service=redis_service)
