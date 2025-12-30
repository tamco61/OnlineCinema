import json
import logging
from datetime import datetime

from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.services.clickhouse import ClickHouseClient

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

        try:
            topics = [
                "stream.start",
                "stream.progress",
                "stream.stop"
            ]

            self.consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )

            await self.consumer.start()
            logger.info(f"Kafka consumer started. Subscribed to: {', '.join(topics)}")

            self.running = True

            # Start consuming messages
            await self._consume_messages()

        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
            raise

    async def stop(self):
        self.running = False

        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def _consume_messages(self):
        try:
            async for message in self.consumer:
                if not self.running:
                    break

                await self._process_message(message)

        except Exception as e:
            logger.error(f"Message consumption error: {e}")

    async def _process_message(self, message):
        try:
            topic = message.topic
            event = message.value

            logger.info(f"📨 Received event from {topic}: user={event.get('user_id')}, movie={event.get('movie_id')}")

            user_id = event.get("user_id")
            movie_id = event.get("movie_id")
            action = event.get("action")
            timestamp = event.get("timestamp")
            position_seconds = event.get("position_seconds", 0)

            event_type = self._map_event_type(action, topic)

            await self._insert_viewing_event(
                user_id=user_id,
                movie_id=movie_id,
                event_type=event_type,
                position_seconds=position_seconds,
                event_time=timestamp,
                metadata=json.dumps(event)
            )

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _map_event_type(self, action: str, topic: str) -> str:
        if "start" in topic or action == "stream_start":
            return "start"
        elif "progress" in topic or action == "progress_update":
            return "progress"
        elif "stop" in topic or action == "stream_stop":
            return "finish"
        else:
            return "unknown"

    async def _insert_viewing_event(
        self,
        user_id: str,
        movie_id: str,
        event_type: str,
        position_seconds: int,
        event_time: str,
        metadata: str
    ):
        try:
            if 'T' in event_time:
                event_datetime = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
            else:
                event_datetime = datetime.fromisoformat(event_time)

            self.ch_client.insert_viewing_event(
                user_id=user_id,
                movie_id=movie_id,
                event_type=event_type,
                position_seconds=position_seconds,
                event_time=event_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                metadata=metadata
            )

            logger.debug(f"Inserted viewing event: {event_type} for user={user_id}, movie={movie_id}")

        except Exception as e:
            logger.error(f"Error inserting viewing event: {e}")
            raise
