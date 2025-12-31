# remote module
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# local module
from services.streaming.app.core.config import settings
from services.streaming.app.api.endpoints.streaming import router

from services.streaming.app.services.s3 import s3_client
from services.streaming.app.services.kafka import kafka
from services.streaming.app.services.redis import cache
from shared.utils.telemetry.metrics import init_metrics

from shared.utils.telemetry.tracer import setup_telemetry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")

    s3_client.connect()
    await cache.connect()
    await kafka.start()

    yield

    await kafka.stop()
    await cache.close()

    logger.info(f"Shutdown {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")

app = FastAPI(
    lifespan=lifespan
)

setup_telemetry(
    app=app,
    service_name=settings.SERVICE_NAME,
    service_version=settings.SERVICE_VERSION,
    environment=settings.ENVIRONMENT,
    otlp_endpoint=settings.OTEL_COLLECTOR_ENDPOINT,
)
init_metrics()

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
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    s3_healthy = False
    redis_healthy = False

    try:
        s3_client.client.list_buckets()
        s3_healthy = True
    except:
        pass

    try:
        if cache.redis:
            await cache.redis.ping()
            redis_healthy = True
    except:
        pass

    return {
        "status": "healthy" if (s3_healthy and redis_healthy) else "degraded",
        "s3": "ok" if s3_healthy else "error",
        "redis": "ok" if redis_healthy else "error",
        "kafka": "enabled" if settings.ENABLE_KAFKA else "disabled"
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
