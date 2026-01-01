from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.user.app.core.config import settings
from services.user.app.db.session import init_db, close_db
from services.user.app.api.router import router
from services.user.app.services.redis import redis_service
from shared.utils.telemetry.metrics import init_metrics
from shared.utils.telemetry.tracer import setup_telemetry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    await redis_service.initialize()
    if settings.is_development:
        await init_db()
        logger.info("Database init")

    yield

    await redis_service.close()
    await close_db()
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


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)
