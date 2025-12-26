# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictStr
from typing import Any, List, Optional
from typing_extensions import Annotated
from uuid import UUID
from openapi_server.models.favorite_response import FavoriteResponse
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.security_api import get_token_HTTPBearer

class BaseFavoritesApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseFavoritesApi.subclasses = BaseFavoritesApi.subclasses + (cls,)
    async def get_favorites_api_v1_users_me_favorites_get(
        self,
        limit: Optional[Annotated[int, Field(le=500, strict=True, ge=1)]],
    ) -> List[FavoriteResponse]:
        """Get user favorites.  Returns user&#39;s favorite/bookmarked content."""
        ...


    async def add_to_favorites_api_v1_users_me_favorites_content_id_post(
        self,
        content_id: UUID,
        content_type: Annotated[StrictStr, Field(description="Content type: movie, series, etc.")],
    ) -> FavoriteResponse:
        """Add content to favorites.  Returns the created favorite entry."""
        ...


    async def remove_from_favorites_api_v1_users_me_favorites_content_id_delete(
        self,
        content_id: UUID,
    ) -> None:
        """Remove content from favorites.  Returns 204 No Content on success."""
        ...
