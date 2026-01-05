import json
import time
import uuid
from datetime import datetime
from typing import Any, Optional

from aiokafka import AIOKafkaProducer

from services.catalog.app.core.config import settings
from shared.utils.telemetry.tracer import trace_span

from shared.utils.telemetry.metrics import counter, histogram


class KafkaProducerService:
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self._initialized = False

    async def initialize(self) -> None:
        start_time = time.monotonic()
        try:
            with trace_span("kafka.initialize"):
                if not settings.ENABLE_KAFKA or self._initialized:
                    return

                self.producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                )
                await self.producer.start()
                self._initialized = True
                logger.info(f"Kafka producer initialized")

        except Exception as e:
            logger.error(f"Kafka initialize error: {e}")
            raise

        finally:
            histogram("kafka_message_processing_seconds").record(time.monotonic() - start_time, {"operation": "initialize"})

    async def close(self) -> None:
        start_time = time.monotonic()
        try:
            with trace_span("kafka.close"):
                if self.producer and self._initialized:
                    await self.producer.stop()
                    self._initialized = False

        except Exception as e:
            logger.error(f"Kafka close error: {e}")
            raise

        finally:
            histogram("kafka_message_processing_seconds").record(time.monotonic() - start_time, {"operation": "close"})

    async def publish_event(
        self,
        topic: str,
        event_data: dict[str, Any],
        key: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> None:
        start_time = time.monotonic()
        try:
            with trace_span(
                "kafka.publish_event",
                {"topic": topic, "event_type": event_type or "unknown"},
            ):
                if not settings.ENABLE_KAFKA or not self._initialized:
                    logger.debug(f"[Kafka disabled] {topic}: {event_data}")
                    return

                key_bytes = key.encode("utf-8") if key else None
                await self.producer.send_and_wait(topic, value=event_data, key=key_bytes)

                counter("kafka_messages_total").add(1, {"event_type": event_type or "unknown"})

        except Exception as e:
            counter("kafka_message_errors_total".add(1, {"event_type": event_type or "unknown"})
            logger.error(f"Kafka publish error [{topic}]: {e}")
            raise

        finally:
            histogram("kafka_message_processing_seconds").record(
                time.monotonic() - start_time,
                {"operation": "publish", "topic": topic},
            )

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
        await self.publish_event(topic, event, key=str(movie_id), event_type="movie.created")

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
        await self.publish_event(topic, event, key=str(movie_id), event_type="movie.updated")

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
        await self.publish_event(topic, event, key=str(movie_id), event_type="movie.published")


kafka_producer = KafkaProducerService()


async def get_kafka_producer() -> KafkaProducerService:
    if not kafka_producer._initialized and settings.ENABLE_KAFKA:
        await kafka_producer.initialize()
    return kafka_producer
