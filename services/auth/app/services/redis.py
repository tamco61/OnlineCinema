import logging
import time
from uuid import UUID
from datetime import timedelta
from typing import Optional

from redis import asyncio as aioredis

from services.auth.app.core.config import settings
from shared.utils.telemetry.tracer import trace_span
from shared.utils.telemetry.metrics import counter, histogram

logger = logging.getLogger(__name__)


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
        start_time = time.monotonic()
        try:
            with trace_span("redis.initialize"):
                if not self._initialized:
                    if self.redis is None:
                        self.redis = await aioredis.from_url(
                            settings.redis_url,
                            encoding="utf-8",
                            decode_responses=True,
                        )
                    self._initialized = True

                counter("redis_calls_total").add(
                    1, {"operation": "initialize"}
                )

        except Exception as e:
            counter("redis_call_errors_total").add(
                1, {"operation": "initialize"}
            )
            logger.error(f"Redis initialization error: {e}")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start_time,
                {"operation": "initialize"},
            )

    async def close(self) -> None:
        start_time = time.monotonic()
        try:
            with trace_span("redis.close"):
                if self.redis and self._initialized:
                    await self.redis.close()
                    self._initialized = False

                counter("redis_calls_total").add(
                    1, {"operation": "close"}
                )

        except Exception as e:
            counter("redis_call_errors_total").add(
                1, {"operation": "close"}
            )
            logger.error(f"Redis close error: {e}")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start_time,
                {"operation": "close"},
            )

    async def store_refresh_token(
            self,
            user_id: UUID,
            token_id: str,
            token_value: str,
            ttl: Optional[timedelta] = None,
    ) -> bool:
        start_time = time.monotonic()
        try:
            with trace_span("redis.store_refresh_token", {"user_id": str(user_id)}):
                if not self._initialized:
                    await self.initialize()

                key = get_refresh_token_key(user_id, token_id)
                if ttl is None:
                    ttl = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

                await self.redis.setex(key, int(ttl.total_seconds()), token_value)

                counter("redis_calls_total").add(
                    1, {"operation": "store_refresh_token"}
                )
                return True

        except Exception as e:
            counter("redis_call_errors_total").add(
                1, {"operation": "store_refresh_token"}
            )
            logger.error(f"Redis store_refresh_token error: {e}")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start_time,
                {"operation": "store_refresh_token"},
            )

    async def get_refresh_token(self, user_id: UUID, token_id: str) -> Optional[str]:
        start_time = time.monotonic()
        try:
            with trace_span("redis.get_refresh_token", {"user_id": str(user_id)}):
                if not self._initialized:
                    await self.initialize()

                key = get_refresh_token_key(user_id, token_id)
                value = await self.redis.get(key)

                counter("redis_calls_total").add(
                    1, {"operation": "get_refresh_token"}
                )

                if value is not None:
                    counter("redis_cache_hits_total").add(
                        1, {"operation": "get_refresh_token"}
                    )
                else:
                    counter("redis_cache_misses_total").add(
                        1, {"operation": "get_refresh_token"}
                    )

                return value

        except Exception as e:
            counter("redis_call_errors_total").add(
                1, {"operation": "get_refresh_token"}
            )
            logger.error(f"Redis get_refresh_token error: {e}")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start_time,
                {"operation": "get_refresh_token"},
            )

    async def delete_refresh_token(self, user_id: UUID, token_id: str) -> bool:
        start_time = time.monotonic()
        try:
            with trace_span("redis.delete_refresh_token", {"user_id": str(user_id)}):
                if not self._initialized:
                    await self.initialize()

                key = get_refresh_token_key(user_id, token_id)
                deleted = await self.redis.delete(key)

                counter("redis_calls_total").add(
                    1, {"operation": "delete_refresh_token"}
                )
                return deleted > 0

        except Exception as e:
            counter("redis_call_errors_total").add(
                1, {"operation": "delete_refresh_token"}
            )
            logger.error(f"Redis delete_refresh_token error: {e}")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start_time,
                {"operation": "delete_refresh_token"},
            )

    async def verify_refresh_token(
        self,
        user_id: UUID,
        token_id: str,
        token_value: str,
    ) -> bool:
        start_time = time.monotonic()
        try:
            with trace_span("redis.verify_refresh_token", {"user_id": str(user_id)}):
                stored_value = await self.get_refresh_token(user_id, token_id)

                counter("redis_calls_total").add(
                    1, {"operation": "verify_refresh_token"}
                )
                return stored_value == token_value if stored_value else False

        except Exception as e:
            counter("redis_call_errors_total").add(
                1, {"operation": "verify_refresh_token"}
            )
            logger.error(f"Redis verify_refresh_token error: {e}")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start_time,
                {"operation": "verify_refresh_token"},
            )

    async def get_user_active_sessions_count(self, user_id: UUID) -> int:
        start_time = time.monotonic()
        try:
            with trace_span(
                "redis.get_user_active_sessions_count",
                {"user_id": str(user_id)},
            ):
                if not self._initialized:
                    await self.initialize()

                pattern = get_user_tokens_pattern(user_id)
                count = 0
                async for _ in self.redis.scan_iter(match=pattern):
                    count += 1

                counter("redis_calls_total").add(
                    1, {"operation": "get_user_active_sessions_count"}
                )
                return count

        except Exception as e:
            counter("redis_call_errors_total").add(
                1, {"operation": "get_user_active_sessions_count"}
            )
            logger.error(f"Redis get_user_active_sessions_count error: {e}")
            raise
        finally:
            histogram("redis_call_duration_seconds").record(
                time.monotonic() - start_time,
                {"operation": "get_user_active_sessions_count"},
            )


redis_service = RedisService()


async def get_redis_service() -> RedisService:
    if not redis_service.get_initialized():
        await redis_service.initialize()
    return redis_service
