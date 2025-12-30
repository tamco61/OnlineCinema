import json
from uuid import UUID
from typing import Any, Optional

from redis import asyncio as aioredis

from app.core.config import settings


class RedisService:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._initialized = False

    def get_initialized(self):
        return self._initialized

    async def initialize(self) -> None:
        if not self._initialized:
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

    async def get_profile(self, user_id: UUID) -> Optional[dict]:
        if not settings.ENABLE_CACHE or not self._initialized:
            return None
        key = f"profile:{user_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_profile(self, user_id: UUID, profile: dict) -> None:
        if not settings.ENABLE_CACHE or not self._initialized:
            return
        key = f"profile:{user_id}"
        await self.redis.setex(
            key,
            settings.REDIS_CACHE_TTL,
            json.dumps(profile, default=str),
        )

    async def delete_profile(self, user_id: UUID) -> None:
        if not self._initialized:
            return
        key = f"profile:{user_id}"
        await self.redis.delete(key)


redis_service = RedisService()


async def get_redis_service() -> RedisService:
    if not redis_service.get_initialized():
        await redis_service.initialize()
    return redis_service
