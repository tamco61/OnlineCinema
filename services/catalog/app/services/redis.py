import json
import uuid
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

    async def get_movie(self, movie_id: uuid.UUID) -> Optional[dict]:
        if not settings.ENABLE_CACHE or not self._initialized:
            return None
        key = f"movie:{movie_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_movie(self, movie_id: uuid.UUID, movie_data: dict) -> None:
        if not settings.ENABLE_CACHE or not self._initialized:
            return
        key = f"movie:{movie_id}"
        await self.redis.setex(
            key,
            settings.REDIS_CACHE_TTL,
            json.dumps(movie_data, default=str),
        )

    async def delete_movie(self, movie_id: uuid.UUID) -> None:
        if not self._initialized:
            return
        key = f"movie:{movie_id}"
        await self.redis.delete(key)

    async def get_popular_movies(self) -> Optional[list]:
        if not settings.ENABLE_CACHE or not self._initialized:
            return None
        key = "movies:popular"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_popular_movies(self, movies: list) -> None:
        if not settings.ENABLE_CACHE or not self._initialized:
            return
        key = "movies:popular"
        await self.redis.setex(
            key,
            settings.REDIS_CACHE_TTL,
            json.dumps(movies, default=str),
        )


redis_service = RedisService()


async def get_redis_service() -> RedisService:
    if not redis_service._initialized:
        await redis_service.initialize()
    return redis_service
