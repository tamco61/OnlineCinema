# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictStr
from typing import Optional
from typing_extensions import Annotated
from uuid import UUID
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.movie_detail_response import MovieDetailResponse
from openapi_server.models.movie_list_response import MovieListResponse


class BaseMoviesPublicApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseMoviesPublicApi.subclasses = BaseMoviesPublicApi.subclasses + (cls,)
    async def get_movies_api_v1_movies_get(
        self,
        page: Optional[Annotated[int, Field(strict=True, ge=1)]],
        page_size: Optional[Annotated[int, Field(le=100, strict=True, ge=1)]],
        search: Optional[StrictStr],
    ) -> MovieListResponse:
        """Get published movies list (public)."""
        ...


    async def get_movie_api_v1_movies_movie_id_get(
        self,
        movie_id: UUID,
    ) -> MovieDetailResponse:
        """Get movie details (public - uses cache)."""
        ...
