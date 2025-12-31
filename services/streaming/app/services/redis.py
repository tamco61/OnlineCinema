import time

import redis.asyncio as redis
import json
import logging

from services.streaming.app.core.config import settings
from shared.utils.telemetry.tracer import trace_span
from shared.utils.telemetry.metrics import counter, histogram

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self):
        self.redis: redis.Redis | None = None

    async def connect(self):
        start_time = time.monotonic()
        try:
            with trace_span("redis.connect"):
                self.redis = await redis.from_url(
                    settings.redis_url,
                    decode_responses=True
                )
                await self.redis.ping()
                counter("redis_calls_total").add(1, {"operation": "connect"})
                logger.info("Connected to Redis")
        except Exception as e:
            counter("redis_call_errors_total").add(1, {"operation": "connect"})
            logger.error(f"Redis connection error: {e}")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(time.monotonic() - start_time, {"operation": "connect"})

    async def close(self):
        start_time = time.monotonic()
        try:
            with trace_span("redis.close"):
                if self.redis:
                    await self.redis.close()
                    counter("redis_calls_total").add(1, {"operation": "close"})
                    logger.info("Redis connection closed")
        except Exception as e:
            counter("redis_call_errors_total").add(1, {"operation": "close"})
            logger.error(f"Redis close error: {e}")
        finally:
            histogram("redis_call_duration_seconds").record(time.monotonic() - start_time, {"operation": "close"})

    async def get_watch_progress(self, user_id: str, movie_id: str) -> dict | None:
        start_time = time.monotonic()
        try:
            with trace_span("redis.get_watch_progress", {"user_id": user_id, "movie_id": movie_id}):
                key = f"progress:{user_id}:{movie_id}"
                data = await self.redis.get(key)
                counter("redis_calls_total").add(1, {"operation": "get_watch_progress"})
                if data:
                    counter("redis_cache_hits_total").add(1, {"cache": "progress"})
                    return json.loads(data)
                counter("redis_cache_misses_total").add(1, {"cache": "progress"})
                return None
        except Exception as e:
            counter("redis_call_errors_total").add(1, {"operation": "get_watch_progress"})
            logger.error(f"Error getting watch progress: {e}")
            return None
        finally:
            histogram("redis_call_duration_seconds").record(time.monotonic() - start_time, {"operation": "get_watch_progress"})

    async def set_watch_progress(self, user_id: str, movie_id: str, position_seconds: int):
        start_time = time.monotonic()
        try:
            with trace_span("redis.set_watch_progress", {"user_id": user_id, "movie_id": movie_id}):
                key = f"progress:{user_id}:{movie_id}"
                data = {
                    "user_id": user_id,
                    "movie_id": movie_id,
                    "position_seconds": position_seconds
                }
                await self.redis.setex(
                    key,
                    settings.REDIS_PROGRESS_TTL,
                    json.dumps(data)
                )
                counter("redis_calls_total").add(1, {"operation": "set_watch_progress"})
                logger.debug(f"Saved progress: {key} = {position_seconds}s")
        except Exception as e:
            counter("redis_call_errors_total").add(1, {"operation": "set_watch_progress"})
            logger.error(f"Error setting watch progress: {e}")
        finally:
            histogram("redis_call_duration_seconds").record(time.monotonic() - start_time, {"operation": "set_watch_progress"})

    async def get_cached_subscription(self, user_id: str) -> dict | None:
        start_time = time.monotonic()
        try:
            with trace_span("redis.get_cached_subscription", {"user_id": user_id}):
                key = f"subscription:{user_id}"
                data = await self.redis.get(key)
                counter("redis_calls_total").add(1, {"operation": "get_cached_subscription"})
                if data:
                    counter("redis_cache_hits_total").add(1, {"cache": "subscription"})
                    logger.debug(f"Cache HIT: subscription:{user_id}")
                    return json.loads(data)
                counter("redis_cache_misses_total").add(1, {"cache": "subscription"})
                logger.debug(f"Cache MISS: subscription:{user_id}")
                return None
        except Exception as e:
            counter("redis_call_errors_total").add(1, {"operation": "get_cached_subscription"})
            logger.error(f"Error getting cached subscription: {e}")
            return None
        finally:
            histogram("redis_call_duration_seconds").record(time.monotonic() - start_time, {"operation": "get_cached_subscription"})

    async def cache_subscription(self, user_id: str, subscription_data: dict):
        start_time = time.monotonic()
        try:
            with trace_span("redis.cache_subscription", {"user_id": user_id}):
                key = f"subscription:{user_id}"
                await self.redis.setex(
                    key,
                    settings.REDIS_SUBSCRIPTION_CACHE_TTL,
                    json.dumps(subscription_data)
                )
                counter("redis_calls_total").add(1, {"operation": "cache_subscription"})
                logger.debug(f"Cached subscription: {user_id}")
        except Exception as e:
            counter("redis_call_errors_total").add(1, {"operation": "cache_subscription"})
            logger.error(f"Error caching subscription: {e}")
        finally:
            histogram("redis_call_duration_seconds").record(time.monotonic() - start_time, {"operation": "cache_subscription"})

    async def invalidate_subscription(self, user_id: str):
        start_time = time.monotonic()
        try:
            with trace_span("redis.invalidate_subscription", {"user_id": user_id}):
                key = f"subscription:{user_id}"
                await self.redis.delete(key)
                counter("redis_calls_total").add(1, {"operation": "invalidate_subscription"})
                logger.debug(f"Invalidated subscription cache: {user_id}")
        except Exception as e:
            counter("redis_call_errors_total").add(1, {"operation": "invalidate_subscription"})
            logger.error(f"Error invalidating subscription: {e}")
        finally:
            histogram("redis_call_duration_seconds").record(time.monotonic() - start_time, {"operation": "invalidate_subscription"})

cache = RedisCache()


async def get_cache() -> RedisCache:
    return cache
