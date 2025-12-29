# remote module
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.db.session import init_db # noqa

# local module
from core.config import settings


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")

    if settings.is_development:
        await init_db()
        logger.info("Database init")

    yield

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

#app.include_router()