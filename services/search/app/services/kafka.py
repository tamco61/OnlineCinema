import time

from aiokafka import AIOKafkaConsumer
import json
import logging
from services.search.app.core.config import settings
from services.search.app.services.search import SearchService
from datetime import datetime

from shared.utils.telemetry.metrics import counter, histogram
from shared.utils.telemetry.tracer import trace_span

logger = logging.getLogger(__name__)


class MovieEventConsumer:
    def __init__(self, search_service: SearchService):
        self.search_service = search_service
        self.consumer: AIOKafkaConsumer | None = None
        self.running = False

    async def start(self):
        if not settings.ENABLE_KAFKA:
            logger.warning("Kafka is disabled. Consumer will not start.")
            return

        async with trace_span("kafka_consumer_start"):
            try:
                topics = [
                    f"{settings.KAFKA_TOPIC_PREFIX}.movie.created",
                    f"{settings.KAFKA_TOPIC_PREFIX}.movie.updated",
                    f"{settings.KAFKA_TOPIC_PREFIX}.movie.published"
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

                await self._consume_messages()

            except Exception as e:
                counter("kafka_message_errors_total").add(1)
                logger.error(f"Kafka consumer error: {e}")
                raise

    async def stop(self):
        async with trace_span("kafka_consumer_stop"):
            self.running = False
            if self.consumer:
                await self.consumer.stop()
                logger.info("Kafka consumer stopped")

    async def _consume_messages(self):
        async with trace_span("kafka_consume_messages"):
            try:
                async for message in self.consumer:
                    if not self.running:
                        break
                    await self._process_message(message)
            except Exception as e:
                counter("kafka_message_errors_total").add(1)
                logger.error(f"Message consumption error: {e}")

    async def _process_message(self, message):
        async with trace_span("kafka_process_message"):
            start_time = time.time()
            counter("kafka_messages_total").add(1)

            try:
                topic = message.topic
                event = message.value
                logger.info(f"Received event from {topic}: {event.get('movie_id')}")

                movie_id = event.get("movie_id")
                action = event.get("action")
                payload = event.get("payload", {})

                if action == "created":
                    await self._handle_movie_created(movie_id, payload)

                elif action == "updated":
                    await self._handle_movie_updated(movie_id, payload)

                elif action == "published":
                    await self._handle_movie_published(movie_id, payload)

                else:
                    logger.warning(f"Unknown action: {action}")

            except Exception as e:
                counter("kafka_message_errors_total").add(1)
                logger.error(f"Error processing message: {e}")
            finally:
                histogram("kafka_message_processing_seconds").record(time.time() - start_time)

    async def _handle_movie_created(self, movie_id: str, payload: dict):
        async with trace_span("kafka_handle_movie_created"):
            logger.info(f"Creating movie index: {movie_id}")
            movie_doc = self._build_movie_document(movie_id, payload)
            await self.search_service.index_movie(movie_doc)

    async def _handle_movie_updated(self, movie_id: str, payload: dict):
        async with trace_span("kafka_handle_movie_updated"):
            logger.info(f"Updating movie index: {movie_id}")
            movie_doc = self._build_movie_document(movie_id, payload)
            await self.search_service.index_movie(movie_doc)

    async def _handle_movie_published(self, movie_id: str, payload: dict):
        async with trace_span("kafka_handle_movie_published"):
            logger.info(f"Publishing movie: {movie_id}")
            is_published = payload.get("is_published", True)
            published_at = payload.get("published_at") or datetime.now().isoformat()
            await self.search_service.update_movie_publish_status(movie_id, is_published, published_at)

    def _build_movie_document(self, movie_id: str, payload: dict) -> dict:
        return {
            "movie_id": movie_id,
            "title": payload.get("title", ""),
            "original_title": payload.get("original_title"),
            "description": payload.get("description"),
            "year": payload.get("year"),
            "duration": payload.get("duration"),
            "rating": payload.get("rating"),
            "age_rating": payload.get("age_rating"),
            "poster_url": payload.get("poster_url"),
            "trailer_url": payload.get("trailer_url"),
            "imdb_id": payload.get("imdb_id"),
            "genres": payload.get("genres", []),
            "actors": payload.get("actors", []),
            "directors": payload.get("directors", []),
            "is_published": payload.get("is_published", False),
            "published_at": payload.get("published_at"),
            "created_at": payload.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat()
        }
