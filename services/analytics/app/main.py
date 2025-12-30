from contextlib import asynccontextmanager
import logging
import asyncio
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.services.kafka import ViewingEventsConsumer
from app.services.clickhouse import clickhouse
from app.api.router import router

logger = logging.getLogger(__name__)

kafka_consumer: ViewingEventsConsumer | None = None
consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle."""
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")

    try:
        clickhouse.ensure_database()
        clickhouse.connect()
        clickhouse.ensure_tables()
        logger.info("ClickHouse initialized successfully")

        if settings.ENABLE_KAFKA:
            kafka_consumer = ViewingEventsConsumer(clickhouse)
            consumer_task = asyncio.create_task(kafka_consumer.start())
            logger.info("Kafka consumer started")
        else:
            logger.warning("Kafka consumer is disabled")

        logger.info(f"{settings.SERVICE_NAME} started successfully")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

    yield

    try:
        if kafka_consumer:
            await kafka_consumer.stop()
            logger.info("Kafka consumer stopped")

        if consumer_task:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass

        clickhouse.close()
        logger.info("ClickHouse connection closed")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")

    logger.info(f"Shutdown {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")


app = FastAPI(
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    try:
        clickhouse.execute("SELECT 1")
        ch_status = "healthy"
    except Exception as e:
        logger.error(f"ClickHouse health check failed: {e}")
        ch_status = "unhealthy"

    kafka_status = "enabled" if settings.ENABLE_KAFKA else "disabled"

    return {
        "status": "healthy" if ch_status == "healthy" else "degraded",
        "clickhouse": ch_status,
        "kafka": kafka_status
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
