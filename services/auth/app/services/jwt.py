from typing import Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from jose import jwt, JWTError

from app.core.config import settings


class JWTService:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(
        self,
        user_id: UUID,
        additional_claims: Optional[dict[str, Any]]=None
    ) -> tuple[str, int]:
        now = datetime.now()
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = now + expires_delta

        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": expire,
            "iat": now,
            "jti": str(uuid4()),
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

        expires_in = int(expires_delta.total_seconds())

        return token, expires_in

    def create_refresh_token(
        self,
        user_id: UUID
    ) -> tuple[str, str, int]:
        now = datetime.now()
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        expire = now + expires_delta

        token_id = str(uuid4())

        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "iat": now,
            "jti": token_id,
        }

        token = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

        expires_in = int(expires_delta.total_seconds())

        return token, token_id, expires_in

    def decode_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return payload
        except JWTError as e:
            raise JWTError(f"Token validation failed: {str(e)}")

    def verify_access_token(self, token: str) -> Optional[UUID]:
        try:
            payload = self.decode_token(token)

            if payload.get("type") != "access":
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            return UUID(user_id)

        except (JWTError, ValueError):
            return None

    def verify_refresh_token(self, token: str) -> Optional[tuple[UUID, str]]:
        try:
            payload = self.decode_token(token)

            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("sub")
            token_id = payload.get("jti")

            if not user_id or not token_id:
                return None

            return UUID(user_id), token_id

        except (JWTError, ValueError):
            return None

    def get_token_expiration(self, token: str) -> Optional[datetime]:
        try:
            payload = self.decode_token(token)
            exp = payload.get("exp")

            if exp:
                return datetime.fromtimestamp(exp)

            return None

        except JWTError:
            return None


jwt_service = JWTService()


async def get_jwt_service() -> JWTService:
    return jwt_service
