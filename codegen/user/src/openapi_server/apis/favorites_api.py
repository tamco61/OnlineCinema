# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.favorites_api_base import BaseFavoritesApi
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
from typing import Any, List, Optional
from typing_extensions import Annotated
from uuid import UUID
from openapi_server.models.favorite_response import FavoriteResponse
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.security_api import get_token_HTTPBearer

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/v1/users/me/favorites",
    responses={
        200: {"model": List[FavoriteResponse], "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Favorites"],
    summary="Get Favorites",
    response_model_by_alias=True,
)
async def get_favorites_api_v1_users_me_favorites_get(
    limit: Optional[Annotated[int, Field(le=500, strict=True, ge=1)]] = Query(100, description="", alias="limit", ge=1, le=500),
    token_HTTPBearer: TokenModel = Security(
        get_token_HTTPBearer
    ),
) -> List[FavoriteResponse]:
    """Get user favorites.  Returns user&#39;s favorite/bookmarked content."""
    if not BaseFavoritesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseFavoritesApi.subclasses[0]().get_favorites_api_v1_users_me_favorites_get(limit)


@router.post(
    "/api/v1/users/me/favorites/{content_id}",
    responses={
        201: {"model": FavoriteResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Favorites"],
    summary="Add To Favorites",
    response_model_by_alias=True,
)
async def add_to_favorites_api_v1_users_me_favorites_content_id_post(
    content_id: UUID = Path(..., description=""),
    content_type: Annotated[StrictStr, Field(description="Content type: movie, series, etc.")] = Query(None, description="Content type: movie, series, etc.", alias="content_type"),
    token_HTTPBearer: TokenModel = Security(
        get_token_HTTPBearer
    ),
) -> FavoriteResponse:
    """Add content to favorites.  Returns the created favorite entry."""
    if not BaseFavoritesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseFavoritesApi.subclasses[0]().add_to_favorites_api_v1_users_me_favorites_content_id_post(content_id, content_type)


@router.delete(
    "/api/v1/users/me/favorites/{content_id}",
    responses={
        204: {"description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Favorites"],
    summary="Remove From Favorites",
    response_model_by_alias=True,
)
async def remove_from_favorites_api_v1_users_me_favorites_content_id_delete(
    content_id: UUID = Path(..., description=""),
    token_HTTPBearer: TokenModel = Security(
        get_token_HTTPBearer
    ),
) -> None:
    """Remove content from favorites.  Returns 204 No Content on success."""
    if not BaseFavoritesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseFavoritesApi.subclasses[0]().remove_from_favorites_api_v1_users_me_favorites_content_id_delete(content_id)
