import json
import logging
import time
from datetime import datetime

from aiokafka import AIOKafkaConsumer

from services.analytics.app.core.config import settings
from services.analytics.app.services.clickhouse import ClickHouseClient

from shared.utils.telemetry.tracer import trace_span, add_span_attribute
from shared.utils.telemetry.metrics import counter, histogram

logger = logging.getLogger(__name__)


class ViewingEventsConsumer:
    def __init__(self, ch_client: ClickHouseClient):
        self.ch_client = ch_client
        self.consumer: AIOKafkaConsumer | None = None
        self.running = False

    async def start(self):
        if not settings.ENABLE_KAFKA:
            logger.warning("Kafka is disabled. Consumer will not start.")
            return

        topics = ["stream.start", "stream.progress", "stream.stop"]

        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP,
            auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )

        await self.consumer.start()
        logger.info("Kafka consumer started", extra={"topics": topics})
        self.running = True

        await self._consume_messages()

    async def stop(self):
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def _consume_messages(self):
        async for message in self.consumer:
            if not self.running:
                break
            await self._process_message(message)

    async def _process_message(self, message):
        start_time = time.monotonic()
        topic = message.topic

        counter("kafka_messages_total").add(
            1,
            attributes={
                "topic": topic,
                "consumer_group": settings.KAFKA_CONSUMER_GROUP,
            },
        )

        try:
            with trace_span(
                "kafka.process_message",
                attributes={
                    "messaging.system": "kafka",
                    "messaging.destination": topic,
                    "messaging.operation": "process",
                },
            ):
                event = message.value

                add_span_attribute("user.id", event.get("user_id"))
                add_span_attribute("movie.id", event.get("movie_id"))

                event_type = self._map_event_type(
                    event.get("action"), topic
                )

                await self._insert_viewing_event(
                    user_id=event.get("user_id"),
                    movie_id=event.get("movie_id"),
                    event_type=event_type,
                    position_seconds=event.get("position_seconds", 0),
                    event_time=event.get("timestamp"),
                    metadata=json.dumps(event),
                )

        except Exception:
            counter("kafka_message_errors_total").add(
                1,
                attributes={"topic": topic},
            )
            logger.exception("Kafka message processing failed")

        finally:
            histogram("kafka_message_processing_seconds").record(
                time.monotonic() - start_time,
                attributes={"topic": topic},
            )

    def _map_event_type(self, action: str, topic: str) -> str:
        if "start" in topic or action == "stream_start":
            return "start"
        if "progress" in topic or action == "progress_update":
            return "progress"
        if "stop" in topic or action == "stream_stop":
            return "finish"
        return "unknown"

    async def _insert_viewing_event(
        self,
        user_id: str,
        movie_id: str,
        event_type: str,
        position_seconds: int,
        event_time: str,
        metadata: str,
    ):
        try:
            if "T" in event_time:
                event_datetime = datetime.fromisoformat(
                    event_time.replace("Z", "+00:00")
                )
            else:
                event_datetime = datetime.fromisoformat(event_time)

            self.ch_client.insert_viewing_event(
                user_id=user_id,
                movie_id=movie_id,
                event_type=event_type,
                position_seconds=position_seconds,
                event_time=event_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                metadata=metadata,
            )

        except Exception:
            add_span_attribute("db.system", "clickhouse")
            add_span_attribute("db.operation", "insert")
            raise
