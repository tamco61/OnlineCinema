# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.movies_admin_api_base import BaseMoviesAdminApi
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
from uuid import UUID
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.movie_create import MovieCreate
from openapi_server.models.movie_response import MovieResponse
from openapi_server.models.movie_update import MovieUpdate


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


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
    if not BaseMoviesAdminApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMoviesAdminApi.subclasses[0]().create_movie_api_v1_movies_post(movie_create)


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
    if not BaseMoviesAdminApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMoviesAdminApi.subclasses[0]().update_movie_api_v1_movies_movie_id_patch(movie_id, movie_update)


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
    if not BaseMoviesAdminApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMoviesAdminApi.subclasses[0]().publish_movie_api_v1_movies_movie_id_publish_post(movie_id)
