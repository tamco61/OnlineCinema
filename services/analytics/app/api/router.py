from fastapi import APIRouter

from app.api.endpoints import analytics

router = APIRouter()

router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)
