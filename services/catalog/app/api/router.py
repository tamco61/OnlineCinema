from fastapi import APIRouter

from app.api.endpoints import catalog

router = APIRouter()

router.include_router(
    catalog.router,
    prefix="/movies",
    tags=["Movies"]
)
