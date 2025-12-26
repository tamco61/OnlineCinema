# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from uuid import UUID
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.movie_create import MovieCreate
from openapi_server.models.movie_response import MovieResponse
from openapi_server.models.movie_update import MovieUpdate


class BaseMoviesAdminApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseMoviesAdminApi.subclasses = BaseMoviesAdminApi.subclasses + (cls,)
    async def create_movie_api_v1_movies_post(
        self,
        movie_create: MovieCreate,
    ) -> MovieResponse:
        """Create movie (admin) - publishes Kafka event."""
        ...


    async def update_movie_api_v1_movies_movie_id_patch(
        self,
        movie_id: UUID,
        movie_update: MovieUpdate,
    ) -> MovieResponse:
        """Update movie (admin) - publishes Kafka event, invalidates cache."""
        ...


    async def publish_movie_api_v1_movies_movie_id_publish_post(
        self,
        movie_id: UUID,
    ) -> MovieResponse:
        """Publish movie (admin) - publishes Kafka event, invalidates cache."""
        ...
