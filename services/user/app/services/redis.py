import json
import time
from uuid import UUID
from typing import Any, Optional

from redis import asyncio as aioredis

from services.user.app.core.config import settings

from shared.utils.telemetry.metrics import counter, histogram
from shared.utils.telemetry.tracer import trace_span


class RedisService:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._initialized = False

    def get_initialized(self):
        return self._initialized

    async def initialize(self) -> None:
        async with trace_span("redis_initialize"):
            start = time.time()
            if not self._initialized:
                try:
                    self.redis = await aioredis.from_url(
                        settings.redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                    )
                    self._initialized = True
                    logger.info("Connected to Redis")
                except Exception as e:
                    counter("redis_call_errors_total").add(1)
                    logger.error(f"Redis initialization error: {e}")
                    if settings.ENABLE_CACHE:
                        raise
            histogram("redis_call_duration_seconds").record(time.time() - start)
            counter("redis_calls_total").add(1)

    async def close(self) -> None:
        async with trace_span("redis_close"):
            start = time.time()
            if self.redis and self._initialized:
                await self.redis.close()
                self._initialized = False
                logger.info("Redis connection closed")
            histogram("redis_call_duration_seconds").record(time.time() - start)
            counter("redis_calls_total").add(1)

    async def get_profile(self, user_id: UUID) -> Optional[dict]:
        async with trace_span("redis_get_profile"):
            start = time.time()
            counter("redis_calls_total").add(1)

            if not settings.ENABLE_CACHE or not self._initialized:
                histogram("redis_call_duration_seconds").record(time.time() - start)
                return None

            key = f"profile:{user_id}"
            try:
                data = await self.redis.get(key)
                if data:
                    counter("redis_cache_hits_total").add(1)
                    return json.loads(data)
                else:
                    counter("redis_cache_misses_total").add(1)
                    return None
            except Exception as e:
                counter("redis_call_errors_total").add(1)
                logger.error(f"Redis get_profile error: {e}")
                return None
            finally:
                histogram("redis_call_duration_seconds").record(time.time() - start)

    async def set_profile(self, user_id: UUID, profile: dict) -> None:
        async with trace_span("redis_set_profile"):
            start = time.time()
            counter("redis_calls_total").add(1)

            if not settings.ENABLE_CACHE or not self._initialized:
                histogram("redis_call_duration_seconds").record(time.time() - start)
                return

            key = f"profile:{user_id}"
            try:
                await self.redis.setex(
                    key,
                    settings.REDIS_CACHE_TTL,
                    json.dumps(profile, default=str),
                )
            except Exception as e:
                counter("redis_call_errors_total").add(1)
                logger.error(f"Redis set_profile error: {e}")
            finally:
                histogram("redis_call_duration_seconds").record(time.time() - start)

    async def delete_profile(self, user_id: UUID) -> None:
        async with trace_span("redis_delete_profile"):
            start = time.time()
            counter("redis_calls_total").add(1)

            if not self._initialized:
                histogram("redis_call_duration_seconds").record(time.time() - start)
                return

            key = f"profile:{user_id}"
            try:
                await self.redis.delete(key)
            except Exception as e:
                counter("redis_call_errors_total").add(1)
                logger.error(f"Redis delete_profile error: {e}")
            finally:
                histogram("redis_call_duration_seconds").record(time.time() - start)


redis_service = RedisService()


async def get_redis_service() -> RedisService:
    if not redis_service.get_initialized():
        await redis_service.initialize()
    return redis_service
