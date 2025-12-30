import logging
import uuid
from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.redis import RedisCache, get_cache
from app.services.s3 import S3Client, get_s3_client
from app.services.kafka import KafkaEventProducer, get_kafka_producer
from app.services.user_client import UserServiceClient, get_user_service_client
from app.db.models import StreamSession, WatchProgress
from app.db.session import get_db

logger = logging.getLogger(__name__)


class StreamingService:
    def __init__(
        self,
        db: AsyncSession,
        s3: S3Client,
        user_client: UserServiceClient,
        kafka: KafkaEventProducer,
        cache: RedisCache
    ):
        self.db = db
        self.s3 = s3
        self.user_client = user_client
        self.kafka = kafka
        self.cache = cache

    async def check_access(self, user_id: str, access_token: str) -> tuple[bool, str]:
        has_subscription = await self.user_client.check_active_subscription(
            user_id,
            access_token
        )

        if not has_subscription:
            return False, "No active subscription"

        return True, "Access granted"

    async def start_stream(
        self,
        user_id: str,
        movie_id: str,
        manifest_type: str = "hls",
        user_agent: str = None,
        ip_address: str = None
    ) -> str:
        manifest_url = self.s3.get_manifest_url(movie_id, manifest_type)

        session = StreamSession(
            user_id=uuid.UUID(user_id),
            movie_id=uuid.UUID(movie_id),
            started_at=datetime.now(),
            user_agent=user_agent,
            ip_address=ip_address
        )

        self.db.add(session)
        await self.db.commit()

        logger.info(f"Started stream session: user={user_id}, movie={movie_id}")

        await self.kafka.publish_stream_start(user_id, movie_id)

        return manifest_url

    async def update_progress(self, user_id: str, movie_id: str, position_seconds: int):
        await self.cache.set_watch_progress(user_id, movie_id, position_seconds)

        await self._sync_progress_to_db(user_id, movie_id, position_seconds)

        await self.kafka.publish_progress_update(user_id, movie_id, position_seconds)

        logger.debug(f"Updated progress: user={user_id}, movie={movie_id}, position={position_seconds}s")

    async def get_progress(self, user_id: str, movie_id: str) -> int:
        progress_data = await self.cache.get_watch_progress(user_id, movie_id)

        if progress_data:
            return progress_data["position_seconds"]

        result = await self.db.execute(
            select(WatchProgress).where(
                WatchProgress.user_id == uuid.UUID(user_id),
                WatchProgress.movie_id == uuid.UUID(movie_id)
            )
        )

        progress = result.scalar_one_or_none()

        if progress:
            await self.cache.set_watch_progress(user_id, movie_id, progress.position_seconds)
            return progress.position_seconds

        return 0

    async def _sync_progress_to_db(self, user_id: str, movie_id: str, position_seconds: int):
        try:
            result = await self.db.execute(
                select(WatchProgress).where(
                    WatchProgress.user_id == uuid.UUID(user_id),
                    WatchProgress.movie_id == uuid.UUID(movie_id)
                )
            )

            progress = result.scalar_one_or_none()

            if progress:
                progress.position_seconds = position_seconds
                progress.updated_at = datetime.now()
                progress.last_watched_at = datetime.now()
            else:
                progress = WatchProgress(
                    user_id=uuid.UUID(user_id),
                    movie_id=uuid.UUID(movie_id),
                    position_seconds=position_seconds,
                    last_watched_at=datetime.now()
                )
                self.db.add(progress)

            await self.db.commit()

            logger.debug(f"Synced progress to DB: user={user_id}, movie={movie_id}")

        except Exception as e:
            logger.error(f"Error syncing progress to DB: {e}")
            await self.db.rollback()

    async def end_stream(self, user_id: str, movie_id: str, position_seconds: int):
        await self.update_progress(user_id, movie_id, position_seconds)

        await self.kafka.publish_stream_stop(user_id, movie_id, position_seconds)

        logger.info(f"Ended stream: user={user_id}, movie={movie_id}, final_position={position_seconds}s")


async def get_streaming_service(
    db: AsyncSession = Depends(get_db),
    s3_client: S3Client = Depends(get_s3_client),
    cache: RedisCache = Depends(get_cache),
    kafka_producer: KafkaEventProducer = Depends(get_kafka_producer),
    user_client: UserServiceClient = Depends(get_user_service_client)
) -> StreamingService:
    return StreamingService(db, s3_client, user_client, kafka_producer, cache)
