from typing import Any, Optional
from uuid import UUID
from datetime import datetime


class JWTService:
    # todo
    def __init__(self):
        # todo
        pass

    def create_access_token(
        self,
        user_id: UUID,
        additional_claim: Optional[dict[str, Any]]=None
    ) -> tuple[str, int]:
        # todo
        pass

    def create_refresh_token(
        self,
        user_id: UUID
    ) -> tuple[str, str, int]:
        # todo
        pass

    def decode_token(self, token: str) -> dict[str, Any]:
        # todo
        pass

    def verify_access_token(self, token: str) -> Optional[UUID]:
        # todo
        pass

    def verify_refresh_token(self, token: str) -> Optional[tuple[UUID, str]]:
        # todo
        pass

    def get_token_expiration(self, token: str) -> Optional[datetime]:
        # todo
        pass


jwt_service = JWTService()


async def get_jwt_service() -> JWTService:
    return jwt_service
