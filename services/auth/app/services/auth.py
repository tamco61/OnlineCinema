import time
from uuid import UUID
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.utils.telemetry.metrics import counter, histogram

from services.auth.app.db.session import get_db
from services.auth.app.db.models import User
from services.auth.app.schemas.auth import AuthResponse, TokenPair, UserResponse, TokenResponse
from services.auth.app.core.security import get_password_hash, verify_password
from services.auth.app.services.jwt import JWTService, get_jwt_service
from services.auth.app.services.redis import RedisService, get_redis_service


def record_metrics(method_name: str, start_time: float, error: bool = False):
    duration = time.monotonic() - start_time
    counter("auth_calls_total").add(1, {"method": method_name})
    histogram("auth_call_duration_seconds").record(duration, {"method": method_name})
    if error:
        counter("auth_call_errors_total").add(1, {"method": method_name})


class AuthService:
    def __init__(self, db: AsyncSession, jwt_service: JWTService, redis_service: RedisService):
        self.db = db
        self.jwt_service = jwt_service
        self.redis_service = redis_service

    async def _create_tokens_for_user(self, user_id: UUID) -> TokenPair:
        method_name = "_create_tokens_for_user"
        start_time = time.monotonic()
        try:
            access_token, access_expires_in = self.jwt_service.create_access_token(user_id)
            refresh_token, token_id, refresh_expires_in = self.jwt_service.create_refresh_token(user_id)

            await self.redis_service.store_refresh_token(
                user_id=user_id,
                token_id=token_id,
                token_value=refresh_token,
            )

            tokens = TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=access_expires_in,
            )

            record_metrics(method_name, start_time)
            return tokens
        except Exception:
            record_metrics(method_name, start_time, error=True)
            raise

    async def register(self, email: str, password: str) -> AuthResponse:
        method_name = "register"
        start_time = time.monotonic()
        try:
            result = await self.db.execute(select(User).where(User.email == email))
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

            record_metrics(method_name, start_time)
            return AuthResponse(user=user_response, tokens=tokens)
        except Exception:
            record_metrics(method_name, start_time, error=True)
            raise

    async def login(self, email: str, password: str) -> AuthResponse:
        method_name = "login"
        start_time = time.monotonic()
        try:
            result = await self.db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if user is None or not verify_password(password, user.password_hash) or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password or inactive user",
                )

            tokens = await self._create_tokens_for_user(user.id)
            user_response = UserResponse.model_validate(user)

            record_metrics(method_name, start_time)
            return AuthResponse(user=user_response, tokens=tokens)
        except Exception:
            record_metrics(method_name, start_time, error=True)
            raise

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        method_name = "refresh_access_token"
        start_time = time.monotonic()
        try:
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

            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user is None or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                )

            access_token, expires_in = self.jwt_service.create_access_token(user_id)
            record_metrics(method_name, start_time)
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=expires_in,
            )
        except Exception:
            record_metrics(method_name, start_time, error=True)
            raise

    async def logout(self, refresh_token: str) -> bool:
        method_name = "logout"
        start_time = time.monotonic()
        try:
            token_data = self.jwt_service.verify_refresh_token(refresh_token)
            if token_data is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            user_id, token_id = token_data
            deleted = await self.redis_service.delete_refresh_token(user_id=user_id, token_id=token_id)
            record_metrics(method_name, start_time)
            return deleted
        except Exception:
            record_metrics(method_name, start_time, error=True)
            raise

    async def logout_all_sessions(self, user_id: UUID) -> int:
        method_name = "logout_all_sessions"
        start_time = time.monotonic()
        try:
            count = await self.redis_service.delete_all_user_tokens(user_id)
            record_metrics(method_name, start_time)
            return count
        except Exception:
            record_metrics(method_name, start_time, error=True)
            raise

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        method_name = "get_user_by_id"
        start_time = time.monotonic()
        try:
            result = await self.db.execute(select(User).where(User.id == user_id))
            record_metrics(method_name, start_time)
            return result.scalar_one_or_none()
        except Exception:
            record_metrics(method_name, start_time, error=True)
            raise

    async def get_user_by_email(self, email: str) -> Optional[User]:
        method_name = "get_user_by_email"
        start_time = time.monotonic()
        try:
            result = await self.db.execute(select(User).where(User.email == email))
            record_metrics(method_name, start_time)
            return result.scalar_one_or_none()
        except Exception:
            record_metrics(method_name, start_time, error=True)
            raise


async def get_auth_service(
        db: AsyncSession = Depends(get_db),
        jwt_service: JWTService = Depends(get_jwt_service),
        redis_service: RedisService = Depends(get_redis_service)
) -> AuthService:
    return AuthService(db=db, jwt_service=jwt_service, redis_service=redis_service)
