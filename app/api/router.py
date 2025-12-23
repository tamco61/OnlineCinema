from fastapi import APIRouter
from app.api import movies
from app.api import users

api_router = APIRouter()
api_router.include_router(movies.router, prefix="/movies", tags=["Movies"])
api_router.include_router(users.router)
