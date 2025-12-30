from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.endpoints.streaming import router
from app.services.s3 import s3_client
from app.services.kafka import kafka
from app.services.redis import cache

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
