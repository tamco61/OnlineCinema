from fastapi import APIRouter
from app.api import movies

api_router = APIRouter()
api_router.include_router(movies.router, prefix="/movies", tags=["Movies"])
