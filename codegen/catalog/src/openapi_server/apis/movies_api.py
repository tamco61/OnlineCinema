# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.movies_api_base import BaseMoviesApi
import openapi_server.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from openapi_server.models.extra_models import TokenModel  # noqa: F401
from pydantic import Field, StrictStr
from typing import Optional
from typing_extensions import Annotated
from uuid import UUID
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.movie_create import MovieCreate
from openapi_server.models.movie_detail_response import MovieDetailResponse
from openapi_server.models.movie_list_response import MovieListResponse
from openapi_server.models.movie_response import MovieResponse
from openapi_server.models.movie_update import MovieUpdate


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/v1/movies",
    responses={
        200: {"model": MovieListResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Movies","Movies - Public"],
    summary="Get Movies",
    response_model_by_alias=True,
)
async def get_movies_api_v1_movies_get(
    page: Optional[Annotated[int, Field(strict=True, ge=1)]] = Query(1, description="", alias="page", ge=1),
    page_size: Optional[Annotated[int, Field(le=100, strict=True, ge=1)]] = Query(20, description="", alias="page_size", ge=1, le=100),
    search: Optional[StrictStr] = Query(None, description="", alias="search"),
) -> MovieListResponse:
    """Get published movies list (public)."""
    if not BaseMoviesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMoviesApi.subclasses[0]().get_movies_api_v1_movies_get(page, page_size, search)


@router.post(
    "/api/v1/movies",
    responses={
        200: {"model": MovieResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Movies","Movies - Admin"],
    summary="Create Movie",
    response_model_by_alias=True,
)
async def create_movie_api_v1_movies_post(
    movie_create: MovieCreate = Body(None, description=""),
) -> MovieResponse:
    """Create movie (admin) - publishes Kafka event."""
    if not BaseMoviesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMoviesApi.subclasses[0]().create_movie_api_v1_movies_post(movie_create)


@router.get(
    "/api/v1/movies/{movie_id}",
    responses={
        200: {"model": MovieDetailResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Movies","Movies - Public"],
    summary="Get Movie",
    response_model_by_alias=True,
)
async def get_movie_api_v1_movies_movie_id_get(
    movie_id: UUID = Path(..., description=""),
) -> MovieDetailResponse:
    """Get movie details (public - uses cache)."""
    if not BaseMoviesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMoviesApi.subclasses[0]().get_movie_api_v1_movies_movie_id_get(movie_id)


@router.patch(
    "/api/v1/movies/{movie_id}",
    responses={
        200: {"model": MovieResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Movies","Movies - Admin"],
    summary="Update Movie",
    response_model_by_alias=True,
)
async def update_movie_api_v1_movies_movie_id_patch(
    movie_id: UUID = Path(..., description=""),
    movie_update: MovieUpdate = Body(None, description=""),
) -> MovieResponse:
    """Update movie (admin) - publishes Kafka event, invalidates cache."""
    if not BaseMoviesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMoviesApi.subclasses[0]().update_movie_api_v1_movies_movie_id_patch(movie_id, movie_update)


@router.post(
    "/api/v1/movies/{movie_id}/publish",
    responses={
        200: {"model": MovieResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Movies","Movies - Admin"],
    summary="Publish Movie",
    response_model_by_alias=True,
)
async def publish_movie_api_v1_movies_movie_id_publish_post(
    movie_id: UUID = Path(..., description=""),
) -> MovieResponse:
    """Publish movie (admin) - publishes Kafka event, invalidates cache."""
    if not BaseMoviesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMoviesApi.subclasses[0]().publish_movie_api_v1_movies_movie_id_publish_post(movie_id)
