# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictBool, StrictStr
from typing import Any, Optional, Union
from typing_extensions import Annotated
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.search_response import SearchResponse
from openapi_server.models.suggest_response import SuggestResponse


class BaseSearchApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSearchApi.subclasses = BaseSearchApi.subclasses + (cls,)
    async def search_movies_api_v1_search_get(
        self,
        query: Annotated[Optional[StrictStr], Field(description="Search query")],
        genres: Annotated[Optional[StrictStr], Field(description="Comma-separated genre slugs (e.g., 'action,drama')")],
        year_from: Annotated[Optional[Annotated[int, Field(le=2100, strict=True, ge=1900)]], Field(description="Minimum year")],
        year_to: Annotated[Optional[Annotated[int, Field(le=2100, strict=True, ge=1900)]], Field(description="Maximum year")],
        rating_from: Annotated[Optional[Union[Annotated[float, Field(le=10.0, strict=True, ge=0.0)], Annotated[int, Field(le=10, strict=True, ge=0)]]], Field(description="Minimum rating")],
        rating_to: Annotated[Optional[Union[Annotated[float, Field(le=10.0, strict=True, ge=0.0)], Annotated[int, Field(le=10, strict=True, ge=0)]]], Field(description="Maximum rating")],
        age_rating: Annotated[Optional[StrictStr], Field(description="Comma-separated age ratings (e.g., 'PG,PG-13')")],
        page: Annotated[Optional[Annotated[int, Field(strict=True, ge=1)]], Field(description="Page number")],
        size: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Page size")],
        published_only: Annotated[Optional[StrictBool], Field(description="Show only published movies")],
    ) -> SearchResponse:
        """Search for movies with full-text search and filters  **Search fields:** - Title (boosted 3x) - Original title (boosted 2x) - Description - Actors (boosted 2x) - Directors (boosted 2x)  **Filters:** - Genres (by slug) - Year range - Rating range - Age rating  **Example:** &#x60;&#x60;&#x60; GET /api/v1/search?query&#x3D;inception&amp;genres&#x3D;sci-fi,action&amp;year_from&#x3D;2010&amp;rating_from&#x3D;8.0 &#x60;&#x60;&#x60;"""
        ...


    async def autocomplete_movies_api_v1_search_suggest_get(
        self,
        query: Annotated[str, Field(min_length=2, strict=True, description="Search query (minimum 2 characters)")],
        limit: Annotated[Optional[Annotated[int, Field(le=20, strict=True, ge=1)]], Field(description="Maximum number of suggestions")],
    ) -> SuggestResponse:
        """Autocomplete suggestions for movie titles  **Returns:** - Top matching movie titles - Sorted by relevance and rating  **Example:** &#x60;&#x60;&#x60; GET /api/v1/search/suggest?query&#x3D;incep&amp;limit&#x3D;5 &#x60;&#x60;&#x60;"""
        ...


    async def health_check_api_v1_search_health_get(
        self,
    ) -> object:
        """Health check endpoint  Verifies Elasticsearch connection"""
        ...
