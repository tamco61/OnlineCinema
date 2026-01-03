from fastapi import APIRouter

from services.user.app.api.endpoints import favorites, history, user

router = APIRouter()

router.include_router(user.router, prefix="/user")
router.include_router(history.router, prefix="/user")
router.include_router(favorites.router, prefix="/user")
