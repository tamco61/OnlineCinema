import json
import hashlib
import logging
import time
from typing import Optional, Dict, Any

import redis.asyncio as aioredis

from shared.utils.telemetry.metrics import counter, histogram

from services.search.app.core.config import settings
from shared.utils.telemetry.tracer import trace_span

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client
        self._initialized = False

    async def initialize(self) -> None:
        async with trace_span("redis_initialize"):
            start = time.time()
            if not self._initialized:
                try:
                    if self.redis is None:
                        self.redis = await aioredis.from_url(
                            settings.redis_url,
                            encoding="utf-8",
                            decode_responses=True
                        )
                        await self.redis.ping()
                        logger.info("Connected to Redis")
                    self._initialized = True
                except Exception as e:
                    counter("redis_call_errors_total").add(1)
                    logger.error(f"Redis connection error: {e}")
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

    @property
    def is_active(self) -> bool:
        return settings.ENABLE_CACHE and self._initialized and self.redis is not None

    def _get_search_key(self, query_hash: str) -> str:
        return f"search:query:{query_hash}"

    async def get_search_results(self, query_hash: str) -> Optional[Dict[str, Any]]:
        async with trace_span("redis_get_search_results"):
            start = time.time()
            counter("redis_calls_total").add(1)

            if not self.is_active:
                histogram("redis_call_duration_seconds").record(time.time() - start)
                return None

            try:
                key = self._get_search_key(query_hash)
                redisd = await self.redis.get(key)

                if redisd:
                    counter("redis_cache_hits_total").add(1)
                    logger.debug(f"Service HIT: {key}")
                    return json.loads(redisd)

                counter("redis_cache_misses_total").add(1)
                logger.debug(f"Service MISS: {key}")
                return None

            except Exception as e:
                counter("redis_call_errors_total").add(1)
                logger.error(f"Redis get error: {e}")
                return None
            finally:
                histogram("redis_call_duration_seconds").record(time.time() - start)

    async def set_search_results(self, query_hash: str, results: Dict[str, Any]) -> bool:
        async with trace_span("redis_set_search_results"):
            start = time.time()
            counter("redis_calls_total").add(1)

            if not self.is_active:
                histogram("redis_call_duration_seconds").record(time.time() - start)
                return False

            try:
                key = self._get_search_key(query_hash)
                await self.redis.setex(
                    key,
                    settings.REDIS_CACHE_TTL,
                    json.dumps(results)
                )
                logger.debug(f"Serviced: {key}")
                return True

            except Exception as e:
                counter("redis_call_errors_total").add(1)
                logger.error(f"Redis set error: {e}")
                return False
            finally:
                histogram("redis_call_duration_seconds").record(time.time() - start)

    async def invalidate_movie(self, movie_id: str) -> None:
        async with trace_span("redis_invalidate_movie"):
            start = time.time()
            counter("redis_calls_total").add(1)

            if not self.is_active:
                histogram("redis_call_duration_seconds").record(time.time() - start)
                return

            try:
                cursor = 0
                pattern = "search:query:*"
                while True:
                    cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        await self.redis.delete(*keys)
                        redis_delete_total = len(keys)
                        counter("redis_calls_total").add(redis_delete_total)
                        logger.debug(f"Invalidated {len(keys)} search cache keys")
                    if cursor == 0:
                        break

            except Exception as e:
                counter("redis_call_errors_total").add(1)
                logger.error(f"Cache invalidation error: {e}")
            finally:
                histogram("redis_call_duration_seconds").record(time.time() - start)

    @staticmethod
    def generate_query_hash(query: str, filters: Dict[str, Any]) -> str:
        query_string = f"{query}_{json.dumps(filters, sort_keys=True)}"
        return hashlib.md5(query_string.encode()).hexdigest()


redis = RedisService()


async def get_redis() -> RedisService:
    if not redis._initialized:
        await redis.initialize()

    return redis
