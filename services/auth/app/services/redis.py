from uuid import UUID
from datetime import timedelta
from typing import Optional

from redis import asyncio as aioredis

from app.core.config import settings


def get_refresh_token_key(user_id: UUID, token_id: str) -> str:
    return f"auth:refresh:{str(user_id)}:{token_id}"


def get_user_tokens_pattern(user_id: UUID) -> str:
    return f"auth:refresh:{str(user_id)}:*"


class RedisService:
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client
        self._initialized = False

    def get_initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        if not self._initialized:
            if self.redis is None:
                self.redis = await aioredis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            self._initialized = True

    async def close(self) -> None:
        if self.redis and self._initialized:
            await self.redis.close()
            self._initialized = False

    async def store_refresh_token(
            self,
            user_id: UUID,
            token_id: str,
            token_value: str,
            ttl: Optional[timedelta] = None,
    ) -> bool:
        if not self._initialized:
            await self.initialize()

        key = get_refresh_token_key(user_id, token_id)

        if ttl is None:
            ttl = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        await self.redis.setex(
            key,
            int(ttl.total_seconds()),
            token_value,
        )

        return True

    async def get_refresh_token(self, user_id: UUID, token_id: str) -> Optional[str]:
        if not self._initialized:
            await self.initialize()

        key = get_refresh_token_key(user_id, token_id)
        return await self.redis.get(key)

    async def delete_refresh_token(self, user_id: UUID, token_id: str) -> bool:
        if not self._initialized:
            await self.initialize()

        key = get_refresh_token_key(user_id, token_id)
        deleted = await self.redis.delete(key)
        return deleted > 0

    async def delete_all_user_tokens(self, user_id: UUID) -> int:
        if not self._initialized:
            await self.initialize()

        pattern = get_user_tokens_pattern(user_id)

        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await self.redis.delete(*keys)

        return 0

    async def verify_refresh_token(self, user_id: UUID, token_id: str, token_value: str) -> bool:
        stored_value = await self.get_refresh_token(user_id, token_id)

        if stored_value is None:
            return False

        return stored_value == token_value

    async def get_user_active_sessions_count(self, user_id: UUID) -> int:
        if not self._initialized:
            await self.initialize()

        pattern = get_user_tokens_pattern(user_id)

        count = 0
        async for _ in self.redis.scan_iter(match=pattern):
            count += 1

        return count


redis_service = RedisService()


async def get_redis_service() -> RedisService:
    if not redis_service.get_initialized():
        await redis_service.initialize()

    return redis_service
