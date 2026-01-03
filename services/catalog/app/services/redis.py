import json
import time
import uuid
from typing import Any, Optional

from redis import asyncio as aioredis

from shared.utils.telemetry.metrics import counter, histogram

from services.catalog.app.core.config import settings
from shared.utils.telemetry.tracer import trace_span


class RedisService:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._initialized = False

    def get_initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        start = time.monotonic()
        try:
            with trace_span("redis.initialize"):
                if not self._initialized:
                    self.redis = await aioredis.from_url(
                        settings.redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                    )
                    self._initialized = True
                    counter("redis_calls_total").add(1, {"operation": "initialize"})
        except Exception as e:
            counter("redis_call_errors_total").add(1, {"operation": "initialize"})
            logger.exception("Redis initialize failed")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start,
                {"operation": "initialize"},
            )

    async def close(self) -> None:
        start = time.monotonic()
        try:
            with trace_span("redis.close"):
                if self.redis and self._initialized:
                    await self.redis.close()
                    self._initialized = False
                    counter("redis_calls_total").add(1, {"operation": "close"})
        except Exception:
            counter("redis_call_errors_total").add(1, {"operation": "close"})
            logger.exception("Redis close failed")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start,
                {"operation": "close"},
            )

    async def get_movie(self, movie_id: uuid.UUID) -> Optional[dict]:
        if not settings.ENABLE_CACHE or not self._initialized:
            return None

        key = f"movie:{movie_id}"
        start = time.monotonic()

        try:
            with trace_span("redis.get_movie", {"movie_id": str(movie_id)}):
                counter("redis_calls_total").add(1, {"operation": "get_movie"})
                data = await self.redis.get(key)

                if data:
                    counter("redis_cache_hits_total").add(1, {"entity": "movie"})
                    return json.loads(data)

                counter("redis_cache_misses_total").add(1, {"entity": "movie"})
                return None

        except Exception:
            redis_call_errors_total.add(1, {"operation": "get_movie"})
            logger.exception("Redis get_movie failed")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start,
                {"operation": "get_movie"},
            )

    async def set_movie(self, movie_id: uuid.UUID, movie_data: dict) -> None:
        if not settings.ENABLE_CACHE or not self._initialized:
            return

        key = f"movie:{movie_id}"
        start = time.monotonic()

        try:
            with trace_span("redis.set_movie", {"movie_id": str(movie_id)}):
                counter("redis_calls_total").add(1, {"operation": "set_movie"})
                await self.redis.setex(
                    key,
                    settings.REDIS_CACHE_TTL,
                    json.dumps(movie_data, default=str),
                )
        except Exception:
            counter("redis_call_errors_total").add(1, {"operation": "set_movie"})
            logger.exception("Redis set_movie failed")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start,
                {"operation": "set_movie"},
            )

    async def delete_movie(self, movie_id: uuid.UUID) -> None:
        if not self._initialized:
            return

        key = f"movie:{movie_id}"
        start = time.monotonic()

        try:
            with trace_span("redis.delete_movie", {"movie_id": str(movie_id)}):
                counter("redis_calls_total").add(1, {"operation": "delete_movie"})
                await self.redis.delete(key)
        except Exception:
            counter("redis_call_errors_total").add(1, {"operation": "delete_movie"})
            logger.exception("Redis delete_movie failed")
            raise
        finally:
            redis_call_duration_seconds.record(
                time.monotonic() - start,
                {"operation": "delete_movie"},
            )

    async def get_popular_movies(self) -> Optional[list]:
        if not settings.ENABLE_CACHE or not self._initialized:
            return None

        key = "movies:popular"
        start = time.monotonic()

        try:
            with trace_span("redis.get_popular_movies"):
                counter("redis_calls_total").add(1, {"operation": "get_popular_movies"})
                data = await self.redis.get(key)

                if data:
                    counter("redis_cache_hits_total").add(1, {"entity": "popular_movies"})
                    return json.loads(data)

                counter("redis_cache_misses_total").add(1, {"entity": "popular_movies"})
                return None

        except Exception:
            counter("redis_call_errors_total").add(1, {"operation": "get_popular_movies"})
            logger.exception("Redis get_popular_movies failed")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start,
                {"operation": "get_popular_movies"},
            )

    async def set_popular_movies(self, movies: list) -> None:
        if not settings.ENABLE_CACHE or not self._initialized:
            return

        key = "movies:popular"
        start = time.monotonic()

        try:
            with trace_span("redis.set_popular_movies"):
                counter("redis_calls_total").add(1, {"operation": "set_popular_movies"})
                await self.redis.setex(
                    key,
                    settings.REDIS_CACHE_TTL,
                    json.dumps(movies, default=str),
                )

        except Exception:
            counter("redis_call_errors_total").add(1, {"operation": "set_popular_movies"})
            logger.exception("Redis set_popular_movies failed")
            raise
        finally:
            redis_call_duration_seconds.record(
                time.monotonic() - start,
                {"operation": "set_popular_movies"},
            )


redis_service = RedisService()


async def get_redis_service() -> RedisService:
    if not redis_service._initialized:
        await redis_service.initialize()
    return redis_service
