from aiokafka import AIOKafkaProducer
import json
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class KafkaEventProducer:
    def __init__(self):
        self.producer: AIOKafkaProducer | None = None

    async def start(self):
        if not settings.ENABLE_KAFKA:
            logger.warning("Kafka is disabled")
            return

        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )

            await self.producer.start()
            logger.info("Kafka producer started")

        except Exception as e:
            logger.error(f"Kafka producer error: {e}")
            if settings.ENABLE_KAFKA:
                raise

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("🔌 Kafka producer stopped")

    async def publish_event(self, topic: str, event: dict, key: str = None):
        if not settings.ENABLE_KAFKA or not self.producer:
            logger.debug(f"Kafka disabled, skipping event: {topic}")
            return

        try:
            key_bytes = key.encode('utf-8') if key else None

            await self.producer.send(
                topic,
                value=event,
                key=key_bytes
            )

            logger.debug(f"Published event to {topic}: {event.get('action', 'unknown')}")

        except Exception as e:
            logger.error(f"Error publishing event to {topic}: {e}")

    async def publish_stream_start(self, user_id: str, movie_id: str):
        topic = f"{settings.KAFKA_TOPIC_PREFIX}.start"

        event = {
            "user_id": user_id,
            "movie_id": movie_id,
            "action": "stream_start",
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.publish_event(topic, event, key=user_id)

    async def publish_stream_stop(self, user_id: str, movie_id: str, position_seconds: int):
        topic = f"{settings.KAFKA_TOPIC_PREFIX}.stop"

        event = {
            "user_id": user_id,
            "movie_id": movie_id,
            "action": "stream_stop",
            "position_seconds": position_seconds,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.publish_event(topic, event, key=user_id)

    async def publish_progress_update(self, user_id: str, movie_id: str, position_seconds: int):
        topic = f"{settings.KAFKA_TOPIC_PREFIX}.progress"

        event = {
            "user_id": user_id,
            "movie_id": movie_id,
            "action": "progress_update",
            "position_seconds": position_seconds,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.publish_event(topic, event, key=user_id)


kafka = KafkaEventProducer()


async def get_kafka_producer() -> KafkaEventProducer:
    return kafka
