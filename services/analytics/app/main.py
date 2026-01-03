from contextlib import asynccontextmanager
import logging
import asyncio
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.analytics.app.core.config import settings
from services.analytics.app.services.kafka import ViewingEventsConsumer
from services.analytics.app.services.clickhouse import clickhouse
from services.analytics.app.api.endpoints.analytics import router
from shared.utils.telemetry.metrics import init_metrics

from shared.utils.telemetry.tracer import setup_telemetry


# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------
# Globals
# ---------------------------
kafka_consumer: ViewingEventsConsumer | None = None
consumer_task: asyncio.Task | None = None


# ---------------------------
# Lifespan
# ---------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle management."""
    global kafka_consumer, consumer_task

    logger.info(
        "Starting service",
        extra={
            "service": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
        },
    )

    # -------- Startup --------
    try:
        clickhouse.ensure_database()
        clickhouse.connect()
        clickhouse.ensure_tables()
        logger.info("ClickHouse initialized")

        if settings.ENABLE_KAFKA:
            kafka_consumer = ViewingEventsConsumer(clickhouse)
            consumer_task = asyncio.create_task(kafka_consumer.start())
            logger.info("Kafka consumer started")
        else:
            logger.warning("Kafka consumer is disabled")

    except Exception as e:
        logger.exception("Startup failed")
        raise

    yield

    # -------- Shutdown --------
    logger.info("Shutting down service")

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

    except Exception:
        logger.exception("Shutdown failed")


# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI(
    title="Analytics Service",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# ---------------------------
# OpenTelemetry (Collector-first)
# ---------------------------
setup_telemetry(
    app=app,
    service_name=settings.SERVICE_NAME,
    service_version=settings.SERVICE_VERSION,
    environment=settings.ENVIRONMENT,
    otlp_endpoint=settings.OTEL_COLLECTOR_ENDPOINT,
)
init_metrics()

# ---------------------------
# Middleware
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Routers
# ---------------------------
app.include_router(router)


# ---------------------------
# Endpoints
# ---------------------------
@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    try:
        clickhouse.execute("SELECT 1")
        ch_status = "healthy"
    except Exception:
        logger.exception("ClickHouse health check failed")
        ch_status = "unhealthy"

    return {
        "status": "healthy" if ch_status == "healthy" else "degraded",
        "clickhouse": ch_status,
        "kafka": "enabled" if settings.ENABLE_KAFKA else "disabled",
    }


# ---------------------------
# Entrypoint
# ---------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
