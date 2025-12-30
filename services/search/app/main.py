import asyncio
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.services.elastic import es_client
from app.services.redis import redis
from app.services.search import get_search_service
from app.services.kafka import MovieEventConsumer
from app.api.router import router

logger = logging.getLogger(__name__)

consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    await es_client.connect()
    logger.info("es start")

    await redis.initialize()
    logger.info("redis start")

    if settings.ENABLE_KAFKA:
        search_service = await get_search_service(es_client, redis)
        consumer = MovieEventConsumer(search_service)
        consumer_task = asyncio.create_task(consumer.start())
        logger.info("kafka start")

    yield

    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("📭 Kafka consumer stopped")

    await es_client.close()
    await redis.close()

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
    es_healthy = False
    redis_healthy = False

    try:
        es_healthy = await es_client.get_client().ping()
    except:
        pass

    try:
        if redis.redis:
            await redis.redis.ping()
            redis_healthy = True
    except:
        pass

    return {
        "status": "healthy" if (es_healthy and redis_healthy) else "degraded",
        "elasticsearch": "ok" if es_healthy else "error",
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
