import redis.asyncio as redis
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self):
        self.redis: redis.Redis | None = None

    async def connect(self):
        try:
            self.redis = await redis.from_url(
                settings.redis_url,
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            raise

    async def close(self):
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def get_watch_progress(self, user_id: str, movie_id: str) -> dict | None:
        try:
            key = f"progress:{user_id}:{movie_id}"
            data = await self.redis.get(key)

            if data:
                return json.loads(data)
            return None

        except Exception as e:
            logger.error(f"Error getting watch progress: {e}")
            return None

    async def set_watch_progress(self, user_id: str, movie_id: str, position_seconds: int):
        try:
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

            logger.debug(f"Saved progress: {key} = {position_seconds}s")

        except Exception as e:
            logger.error(f"Error setting watch progress: {e}")

    async def get_cached_subscription(self, user_id: str) -> dict | None:
        try:
            key = f"subscription:{user_id}"
            data = await self.redis.get(key)

            if data:
                logger.debug(f"Cache HIT: subscription:{user_id}")
                return json.loads(data)

            logger.debug(f"Cache MISS: subscription:{user_id}")
            return None

        except Exception as e:
            logger.error(f"Error getting cached subscription: {e}")
            return None

    async def cache_subscription(self, user_id: str, subscription_data: dict):
        try:
            key = f"subscription:{user_id}"

            await self.redis.setex(
                key,
                settings.REDIS_SUBSCRIPTION_CACHE_TTL,
                json.dumps(subscription_data)
            )

            logger.debug(f"Cached subscription: {user_id}")

        except Exception as e:
            logger.error(f"Error caching subscription: {e}")

    async def invalidate_subscription(self, user_id: str):
        try:
            key = f"subscription:{user_id}"
            await self.redis.delete(key)
            logger.debug(f"Invalidated subscription cache: {user_id}")

        except Exception as e:
            logger.error(f"Error invalidating subscription: {e}")


cache = RedisCache()


async def get_cache() -> RedisCache:
    return cache
