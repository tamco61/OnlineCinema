# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.user_profile_response import UserProfileResponse
from openapi_server.models.user_profile_update import UserProfileUpdate
from openapi_server.security_api import get_token_HTTPBearer

class BaseUsersApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseUsersApi.subclasses = BaseUsersApi.subclasses + (cls,)
    async def get_my_profile_api_v1_users_me_get(
        self,
    ) -> UserProfileResponse:
        """Get current user profile.  Creates profile automatically if doesn&#39;t exist."""
        ...


    async def update_my_profile_api_v1_users_me_patch(
        self,
        user_profile_update: UserProfileUpdate,
    ) -> UserProfileResponse:
        """Update current user profile.  Updates only provided fields."""
        ...
