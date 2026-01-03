from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.auth.app.core.config import settings
from services.auth.app.db.session import init_db, close_db
from services.auth.app.api.router import api_router
from services.auth.app.services.redis import redis_service
from shared.utils.telemetry.metrics import init_metrics
from shared.utils.telemetry.tracer import setup_telemetry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    print(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")

    await redis_service.initialize()
    print("redis start")

    if settings.is_development:
        await init_db()
        print("Database init")

    yield

    await redis_service.close()
    await close_db()
    print(f"Shutdown {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")


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


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn

    print(settings.HOST, settings.PORT)
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )
