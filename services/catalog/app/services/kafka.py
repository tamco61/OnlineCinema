"""
Kafka producer service for publishing events.

Events:
- catalog.movie.created
- catalog.movie.updated
- catalog.movie.published
"""

import json
import uuid
from datetime import datetime
from typing import Any, Optional

from aiokafka import AIOKafkaProducer

from app.core.config import settings


class KafkaProducerService:
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self._initialized = False

    async def initialize(self) -> None:
        if not settings.ENABLE_KAFKA or self._initialized:
            return

        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            await self.producer.start()
            self._initialized = True
            print(f"Kafka producer connected to {settings.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            print(f"Kafka producer failed to start: {e}")
            self._initialized = False

    async def close(self) -> None:
        if self.producer and self._initialized:
            await self.producer.stop()
            self._initialized = False

    async def publish_event(
        self,
        topic: str,
        event_data: dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        if not settings.ENABLE_KAFKA or not self._initialized:
            print(f"[Kafka disabled] Would publish to {topic}: {event_data}")
            return

        try:
            key_bytes = key.encode("utf-8") if key else None
            await self.producer.send_and_wait(topic, value=event_data, key=key_bytes)
            print(f"[Kafka] Published to {topic}: {event_data.get('action')}")
        except Exception as e:
            print(f"[Kafka] Failed to publish to {topic}: {e}")

    async def publish_movie_created(self, movie_id: uuid.UUID, movie_data: dict) -> None:
        topic = f"{settings.KAFKA_TOPIC_PREFIX}.movie.created"
        event = {
            "movie_id": str(movie_id),
            "action": "created",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "title": movie_data.get("title"),
                "year": movie_data.get("year"),
                "rating": movie_data.get("rating"),
                "is_published": movie_data.get("is_published", False),
            },
        }
        await self.publish_event(topic, event, key=str(movie_id))

    async def publish_movie_updated(self, movie_id: uuid.UUID, movie_data: dict) -> None:
        topic = f"{settings.KAFKA_TOPIC_PREFIX}.movie.updated"
        event = {
            "movie_id": str(movie_id),
            "action": "updated",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "title": movie_data.get("title"),
                "year": movie_data.get("year"),
                "rating": movie_data.get("rating"),
                "is_published": movie_data.get("is_published"),
            },
        }
        await self.publish_event(topic, event, key=str(movie_id))

    async def publish_movie_published(self, movie_id: uuid.UUID, movie_data: dict) -> None:
        topic = f"{settings.KAFKA_TOPIC_PREFIX}.movie.published"
        event = {
            "movie_id": str(movie_id),
            "action": "published",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "title": movie_data.get("title"),
                "year": movie_data.get("year"),
                "published_at": movie_data.get("published_at"),
            },
        }
        await self.publish_event(topic, event, key=str(movie_id))


kafka_producer = KafkaProducerService()


async def get_kafka_producer() -> KafkaProducerService:
    if not kafka_producer._initialized and settings.ENABLE_KAFKA:
        await kafka_producer.initialize()
    return kafka_producer
