from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional

from app.db.session import get_db # noqa
from app.db.models import User # noqa
from app.schemas.auth import AuthResponse, TokenPair, UserResponse, TokenResponse # noqa
from app.core.security import get_password_hash, verify_password # noqa

from .jwt import JWTService, get_jwt_service


class AuthService:
    def __init__(self, db: AsyncSession, jwt_service: JWTService):
        self.db = db
        self.jwt_service = jwt_service

    async def _create_tokens_for_user(self, user_id: UUID) -> TokenPair:
        access_token, access_expires_in = self.jwt_service.create_access_token(user_id)
        refresh_token, token_id, refresh_expires_in = self.jwt_service.create_refresh_token(user_id)

        # todo: add Redis
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

        tokens = self._create_tokens_for_user(new_user.id)

        user_response = UserResponse.model_validate(new_user)
        return AuthResponse(user=user_response, tokens=tokens)

    async def login(self, email: str, password: str) -> AuthResponse:
        # todo
        pass

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        # todo
        pass

    async def logout(self, refresh_token: str) -> bool:
        # todo
        pass

    async def logout_all_sessions(self, user_id: UUID) -> int:
        # todo
        pass

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        # todo
        pass

    async def get_user_by_email(self, email: str) -> Optional[User]:
        # todo
        pass


async def get_auth_service(
        db: AsyncSession = Depends(get_db),
        jwt_service: JWTService = Depends(get_jwt_service)) -> AuthService:
    return AuthService(db=db, jwt_service=jwt_service)
