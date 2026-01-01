from fastapi import APIRouter

from app.api.endpoints import streaming

router = APIRouter()

router.include_router(
    streaming.router,
    prefix="/stream",
    tags=["Streaming"]
)
