# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field
from typing import List, Optional
from typing_extensions import Annotated
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.watch_history_response import WatchHistoryResponse
from openapi_server.models.watch_history_update import WatchHistoryUpdate
from openapi_server.security_api import get_token_HTTPBearer

class BaseHistoryApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseHistoryApi.subclasses = BaseHistoryApi.subclasses + (cls,)
    async def get_watch_history_api_v1_users_me_history_get(
        self,
        limit: Optional[Annotated[int, Field(le=100, strict=True, ge=1)]],
    ) -> List[WatchHistoryResponse]:
        """Get user watch history.  Returns recently watched content ordered by last watched time."""
        ...


    async def update_watch_progress_api_v1_users_me_history_post(
        self,
        watch_history_update: WatchHistoryUpdate,
    ) -> WatchHistoryResponse:
        """Update watch progress for content.  Creates new history entry if doesn&#39;t exist, updates if exists."""
        ...
