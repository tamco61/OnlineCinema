import time

from aiokafka import AIOKafkaProducer
import json
from datetime import datetime
from services.streaming.app.core.config import settings
import logging

from shared.utils.telemetry.tracer import trace_span
from shared.utils.telemetry.metrics import counter, histogram

logger = logging.getLogger(__name__)


class KafkaEventProducer:
    def __init__(self):
        self.producer: AIOKafkaProducer | None = None
        self._initialized = False

    async def start(self):
        start_time = time.monotonic()
        try:
            with trace_span("kafka.start"):
                if not settings.ENABLE_KAFKA:
                    logger.warning("Kafka is disabled")
                    return

                if self._initialized:
                    return

                self.producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )

                await self.producer.start()
                self._initialized = True
                logger.info("Kafka producer started")

        except Exception as e:
            counter("kafka_message_errors_total").add(1, {"operation": "start"})
            logger.error(f"Kafka producer start error: {e}")
            if settings.ENABLE_KAFKA:
                raise
        finally:
            histogram("kafka_message_processing_seconds").record(time.monotonic() - start_time, {"operation": "start"})

    async def stop(self):
        start_time = time.monotonic()
        try:
            with trace_span("kafka.stop"):
                if self.producer:
                    await self.producer.stop()
                    self._initialized = False
                    logger.info("Kafka producer stopped")
        except Exception as e:
            counter("kafka_message_errors_total").add(1, {"operation": "stop"})
            logger.error(f"Kafka producer stop error: {e}")
        finally:
            histogram("kafka_message_processing_seconds").record(time.monotonic() - start_time, {"operation": "stop"})

    async def publish_event(self, topic: str, event: dict, key: str = None):
        start_time = time.monotonic()
        try:
            with trace_span("kafka.publish_event", {"topic": topic, "key": key}):
                if not settings.ENABLE_KAFKA or not self.producer:
                    logger.debug(f"Kafka disabled, skipping event: {topic}")
                    return

                key_bytes = key.encode('utf-8') if key else None

                await self.producer.send_and_wait(
                    topic,
                    value=event,
                    key=key_bytes
                )

                counter("kafka_messages_total").add(1, {"topic": topic})
                logger.debug(f"Published event to {topic}: {event.get('action', 'unknown')}")

        except Exception as e:
            counter("kafka_message_errors_total").add(1, {"topic": topic})
            logger.error(f"Error publishing event to {topic}: {e}")
        finally:
            histogram("kafka_message_processing_seconds").record(time.monotonic() - start_time, {"topic": topic})

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
