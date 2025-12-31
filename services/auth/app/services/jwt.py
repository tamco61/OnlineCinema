from typing import Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from jose import jwt, JWTError
import time

from shared.utils.telemetry.metrics import counter, histogram

from services.auth.app.core.config import settings

class JWTService:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def _record_metrics(self, operation: str, start_time: float, error: bool = False):
        counter("jwt_calls_total").add(1, {"operation": operation})
        histogram("jwt_call_duration_seconds").record(time.monotonic() - start_time, {"operation": operation})
        if error:
            counter("jwt_call_errors_total").add(1, {"operation": operation})

    def create_access_token(
        self,
        user_id: UUID,
        additional_claims: Optional[dict[str, Any]] = None
    ) -> tuple[str, int]:
        start_time = time.monotonic()
        try:
            now = datetime.now()
            expire = now + timedelta(minutes=self.access_token_expire_minutes)

            payload = {
                "sub": str(user_id),
                "type": "access",
                "exp": expire,
                "iat": now,
                "jti": str(uuid4()),
            }
            if additional_claims:
                payload.update(additional_claims)

            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            expires_in = int(timedelta(minutes=self.access_token_expire_minutes).total_seconds())

            self._record_metrics("create_access_token", start_time)
            return token, expires_in
        except Exception:
            self._record_metrics("create_access_token", start_time, error=True)
            raise

    def create_refresh_token(
        self,
        user_id: UUID
    ) -> tuple[str, str, int]:
        start_time = time.monotonic()
        try:
            now = datetime.now()
            expire = now + timedelta(days=self.refresh_token_expire_days)
            token_id = str(uuid4())

            payload = {
                "sub": str(user_id),
                "type": "refresh",
                "exp": expire,
                "iat": now,
                "jti": token_id,
            }

            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            expires_in = int(timedelta(days=self.refresh_token_expire_days).total_seconds())

            self._record_metrics("create_refresh_token", start_time)
            return token, token_id, expires_in
        except Exception:
            self._record_metrics("create_refresh_token", start_time, error=True)
            raise

    def decode_token(self, token: str) -> dict[str, Any]:
        start_time = time.monotonic()
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            self._record_metrics("decode_token", start_time)
            return payload
        except JWTError as e:
            self._record_metrics("decode_token", start_time, error=True)
            raise JWTError(f"Token validation failed: {str(e)}")

    def verify_access_token(self, token: str) -> Optional[UUID]:
        start_time = time.monotonic()
        try:
            payload = self.decode_token(token)
            if payload.get("type") != "access":
                self._record_metrics("verify_access_token", start_time)
                return None
            user_id = payload.get("sub")
            if not user_id:
                self._record_metrics("verify_access_token", start_time)
                return None
            self._record_metrics("verify_access_token", start_time)
            return UUID(user_id)
        except (JWTError, ValueError):
            self._record_metrics("verify_access_token", start_time, error=True)
            return None

    def verify_refresh_token(self, token: str) -> Optional[tuple[UUID, str]]:
        start_time = time.monotonic()
        try:
            payload = self.decode_token(token)
            if payload.get("type") != "refresh":
                self._record_metrics("verify_refresh_token", start_time)
                return None
            user_id = payload.get("sub")
            token_id = payload.get("jti")
            if not user_id or not token_id:
                self._record_metrics("verify_refresh_token", start_time)
                return None
            self._record_metrics("verify_refresh_token", start_time)
            return UUID(user_id), token_id
        except (JWTError, ValueError):
            self._record_metrics("verify_refresh_token", start_time, error=True)
            return None

    def get_token_expiration(self, token: str) -> Optional[datetime]:
        start_time = time.monotonic()
        try:
            payload = self.decode_token(token)
            exp = payload.get("exp")
            result = datetime.fromtimestamp(exp) if exp else None
            self._record_metrics("get_token_expiration", start_time)
            return result
        except JWTError:
            self._record_metrics("get_token_expiration", start_time, error=True)
            return None


# -----------------------------
# Singleton / Dependency
# -----------------------------
jwt_service = JWTService()

async def get_jwt_service() -> JWTService:
    return jwt_service
