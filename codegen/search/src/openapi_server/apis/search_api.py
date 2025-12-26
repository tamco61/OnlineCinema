# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.search_api_base import BaseSearchApi
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
from pydantic import Field, StrictBool, StrictStr
from typing import Any, Optional, Union
from typing_extensions import Annotated
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.search_response import SearchResponse
from openapi_server.models.suggest_response import SuggestResponse


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/v1/search",
    responses={
        200: {"model": SearchResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Search"],
    summary="Search Movies",
    response_model_by_alias=True,
)
async def search_movies_api_v1_search_get(
    query: Annotated[Optional[StrictStr], Field(description="Search query")] = Query(None, description="Search query", alias="query"),
    genres: Annotated[Optional[StrictStr], Field(description="Comma-separated genre slugs (e.g., 'action,drama')")] = Query(None, description="Comma-separated genre slugs (e.g., &#39;action,drama&#39;)", alias="genres"),
    year_from: Annotated[Optional[Annotated[int, Field(le=2100, strict=True, ge=1900)]], Field(description="Minimum year")] = Query(None, description="Minimum year", alias="year_from", ge=1900, le=2100),
    year_to: Annotated[Optional[Annotated[int, Field(le=2100, strict=True, ge=1900)]], Field(description="Maximum year")] = Query(None, description="Maximum year", alias="year_to", ge=1900, le=2100),
    rating_from: Annotated[Optional[Union[Annotated[float, Field(le=10.0, strict=True, ge=0.0)], Annotated[int, Field(le=10, strict=True, ge=0)]]], Field(description="Minimum rating")] = Query(None, description="Minimum rating", alias="rating_from"),
    rating_to: Annotated[Optional[Union[Annotated[float, Field(le=10.0, strict=True, ge=0.0)], Annotated[int, Field(le=10, strict=True, ge=0)]]], Field(description="Maximum rating")] = Query(None, description="Maximum rating", alias="rating_to"),
    age_rating: Annotated[Optional[StrictStr], Field(description="Comma-separated age ratings (e.g., 'PG,PG-13')")] = Query(None, description="Comma-separated age ratings (e.g., &#39;PG,PG-13&#39;)", alias="age_rating"),
    page: Annotated[Optional[Annotated[int, Field(strict=True, ge=1)]], Field(description="Page number")] = Query(1, description="Page number", alias="page", ge=1),
    size: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Page size")] = Query(20, description="Page size", alias="size", ge=1, le=100),
    published_only: Annotated[Optional[StrictBool], Field(description="Show only published movies")] = Query(True, description="Show only published movies", alias="published_only"),
) -> SearchResponse:
    """Search for movies with full-text search and filters  **Search fields:** - Title (boosted 3x) - Original title (boosted 2x) - Description - Actors (boosted 2x) - Directors (boosted 2x)  **Filters:** - Genres (by slug) - Year range - Rating range - Age rating  **Example:** &#x60;&#x60;&#x60; GET /api/v1/search?query&#x3D;inception&amp;genres&#x3D;sci-fi,action&amp;year_from&#x3D;2010&amp;rating_from&#x3D;8.0 &#x60;&#x60;&#x60;"""
    if not BaseSearchApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSearchApi.subclasses[0]().search_movies_api_v1_search_get(query, genres, year_from, year_to, rating_from, rating_to, age_rating, page, size, published_only)


@router.get(
    "/api/v1/search/suggest",
    responses={
        200: {"model": SuggestResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Search"],
    summary="Autocomplete Movies",
    response_model_by_alias=True,
)
async def autocomplete_movies_api_v1_search_suggest_get(
    query: Annotated[str, Field(min_length=2, strict=True, description="Search query (minimum 2 characters)")] = Query(None, description="Search query (minimum 2 characters)", alias="query", min_length=2),
    limit: Annotated[Optional[Annotated[int, Field(le=20, strict=True, ge=1)]], Field(description="Maximum number of suggestions")] = Query(10, description="Maximum number of suggestions", alias="limit", ge=1, le=20),
) -> SuggestResponse:
    """Autocomplete suggestions for movie titles  **Returns:** - Top matching movie titles - Sorted by relevance and rating  **Example:** &#x60;&#x60;&#x60; GET /api/v1/search/suggest?query&#x3D;incep&amp;limit&#x3D;5 &#x60;&#x60;&#x60;"""
    if not BaseSearchApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSearchApi.subclasses[0]().autocomplete_movies_api_v1_search_suggest_get(query, limit)


@router.get(
    "/api/v1/search/health",
    responses={
        200: {"model": object, "description": "Successful Response"},
    },
    tags=["Search"],
    summary="Health Check",
    response_model_by_alias=True,
)
async def health_check_api_v1_search_health_get(
) -> object:
    """Health check endpoint  Verifies Elasticsearch connection"""
    if not BaseSearchApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSearchApi.subclasses[0]().health_check_api_v1_search_health_get()
