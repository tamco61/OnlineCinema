# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from openapi_server.models.auth_response import AuthResponse
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.logout_request import LogoutRequest
from openapi_server.models.message_response import MessageResponse
from openapi_server.models.token_refresh import TokenRefresh
from openapi_server.models.token_response import TokenResponse
from openapi_server.models.user_login import UserLogin
from openapi_server.models.user_register import UserRegister
from openapi_server.models.user_response import UserResponse
from openapi_server.security_api import get_token_HTTPBearer

class BaseAuthenticationApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseAuthenticationApi.subclasses = BaseAuthenticationApi.subclasses + (cls,)
    async def register_api_v1_auth_register_post(
        self,
        user_register: UserRegister,
    ) -> AuthResponse:
        """Create a new user account with email and password"""
        ...


    async def login_api_v1_auth_login_post(
        self,
        user_login: UserLogin,
    ) -> AuthResponse:
        """Authenticate user and receive access and refresh tokens"""
        ...


    async def refresh_token_api_v1_auth_refresh_post(
        self,
        token_refresh: TokenRefresh,
    ) -> TokenResponse:
        """Get a new access token using a valid refresh token"""
        ...


    async def logout_api_v1_auth_logout_post(
        self,
        logout_request: LogoutRequest,
    ) -> MessageResponse:
        """Invalidate refresh token (logout from current device)"""
        ...


    async def logout_all_api_v1_auth_logout_all_post(
        self,
    ) -> MessageResponse:
        """Invalidate all refresh tokens for the authenticated user"""
        ...


    async def get_current_user_info_api_v1_auth_me_get(
        self,
    ) -> UserResponse:
        """Get information about the authenticated user"""
        ...
