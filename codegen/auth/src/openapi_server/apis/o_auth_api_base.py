# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictStr
from typing import Optional
from typing_extensions import Annotated
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.message_response import MessageResponse
from openapi_server.models.o_auth_authorization_response import OAuthAuthorizationResponse
from openapi_server.models.o_auth_callback_response import OAuthCallbackResponse


class BaseOAuthApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseOAuthApi.subclasses = BaseOAuthApi.subclasses + (cls,)
    async def google_oauth_init_api_v1_auth_oauth_google_get(
        self,
        redirect_uri: Annotated[Optional[StrictStr], Field(description="Optional redirect URI after auth")],
    ) -> OAuthAuthorizationResponse:
        """Get Google OAuth authorization URL"""
        ...


    async def google_oauth_callback_api_v1_auth_oauth_google_callback_get(
        self,
        code: Annotated[StrictStr, Field(description="Authorization code from Google")],
        state: Annotated[StrictStr, Field(description="State parameter for CSRF protection")],
    ) -> MessageResponse:
        """Handle Google OAuth callback (redirect endpoint)"""
        ...


    async def google_oauth_token_exchange_api_v1_auth_oauth_google_callback_post(
        self,
        code: Annotated[StrictStr, Field(description="Authorization code from Google")],
        state: Annotated[StrictStr, Field(description="State parameter")],
    ) -> None:
        """Exchange authorization code for user tokens (for SPA/mobile apps)"""
        ...
