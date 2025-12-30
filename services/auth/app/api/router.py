from fastapi import APIRouter

from app.api.endpoints import auth

router = APIRouter()

router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)