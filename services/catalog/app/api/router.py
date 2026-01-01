from fastapi import APIRouter

from services.catalog.app.api.endpoints import catalog

router = APIRouter()

router.include_router(
    catalog.router,
    prefix="/movies",
    tags=["Movies"]
)
