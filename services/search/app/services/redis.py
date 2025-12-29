import json
import hashlib
import logging
from typing import Optional, Dict, Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client
        self._initialized = False

    async def initialize(self) -> None:
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
                logger.error(f"Redis connection error: {e}")
                if settings.ENABLE_CACHE:
                    raise

    async def close(self) -> None:
        if self.redis and self._initialized:
            await self.redis.close()
            self._initialized = False
            logger.info("🔌 Redis connection closed")

    @property
    def is_active(self) -> bool:
        return settings.ENABLE_CACHE and self._initialized and self.redis is not None

    def _get_search_key(self, query_hash: str) -> str:

        return f"search:query:{query_hash}"

    async def get_search_results(self, query_hash: str) -> Optional[Dict[str, Any]]:
        if not self.is_active:
            return None

        try:
            key = self._get_search_key(query_hash)
            redisd = await self.redis.get(key)

            if redisd:
                logger.debug(f"✅ Service HIT: {key}")
                return json.loads(redisd)

            logger.debug(f"❌ Service MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set_search_results(self, query_hash: str, results: Dict[str, Any]) -> bool:
        if not self.is_active:
            return False

        try:
            key = self._get_search_key(query_hash)
            await self.redis.setex(
                key,
                settings.REDIS_CACHE_TTL,
                json.dumps(results)
            )
            logger.debug(f"💾 Serviced: {key}")
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def invalidate_movie(self, movie_id: str) -> None:
        if not self.is_active:
            return

        try:
            cursor = 0
            pattern = "search:query:*"

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                    logger.debug(f"Invalidated {len(keys)} search cache keys")

                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    @staticmethod
    def generate_query_hash(query: str, filters: Dict[str, Any]) -> str:
        query_string = f"{query}_{json.dumps(filters, sort_keys=True)}"
        return hashlib.md5(query_string.encode()).hexdigest()


redis = RedisService()


async def get_redis() -> RedisService:
    if not redis._initialized:
        await redis.initialize()

    return redis