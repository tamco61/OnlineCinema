from fastapi import APIRouter

from app.api.endpoints import search

router = APIRouter()

router.include_router(
    search.router,
    prefix="/search",
    tags=["Search"]
)
