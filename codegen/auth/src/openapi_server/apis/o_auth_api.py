# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.o_auth_api_base import BaseOAuthApi
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
from typing import Optional
from typing_extensions import Annotated
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.message_response import MessageResponse
from openapi_server.models.o_auth_authorization_response import OAuthAuthorizationResponse
from openapi_server.models.o_auth_callback_response import OAuthCallbackResponse


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/v1/auth/oauth/google",
    responses={
        200: {"model": OAuthAuthorizationResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["OAuth"],
    summary="Initiate Google OAuth",
    response_model_by_alias=True,
)
async def google_oauth_init_api_v1_auth_oauth_google_get(
    redirect_uri: Annotated[Optional[StrictStr], Field(description="Optional redirect URI after auth")] = Query(None, description="Optional redirect URI after auth", alias="redirect_uri"),
) -> OAuthAuthorizationResponse:
    """Get Google OAuth authorization URL"""
    if not BaseOAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseOAuthApi.subclasses[0]().google_oauth_init_api_v1_auth_oauth_google_get(redirect_uri)


@router.get(
    "/api/v1/auth/oauth/google/callback",
    responses={
        200: {"model": MessageResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["OAuth"],
    summary="Google OAuth callback",
    response_model_by_alias=True,
)
async def google_oauth_callback_api_v1_auth_oauth_google_callback_get(
    code: Annotated[StrictStr, Field(description="Authorization code from Google")] = Query(None, description="Authorization code from Google", alias="code"),
    state: Annotated[StrictStr, Field(description="State parameter for CSRF protection")] = Query(None, description="State parameter for CSRF protection", alias="state"),
) -> MessageResponse:
    """Handle Google OAuth callback (redirect endpoint)"""
    if not BaseOAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseOAuthApi.subclasses[0]().google_oauth_callback_api_v1_auth_oauth_google_callback_get(code, state)


@router.post(
    "/api/v1/auth/oauth/google/callback",
    responses={
        501: {"model": OAuthCallbackResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["OAuth"],
    summary="Process Google OAuth code",
    response_model_by_alias=True,
)
async def google_oauth_token_exchange_api_v1_auth_oauth_google_callback_post(
    code: Annotated[StrictStr, Field(description="Authorization code from Google")] = Query(None, description="Authorization code from Google", alias="code"),
    state: Annotated[StrictStr, Field(description="State parameter")] = Query(None, description="State parameter", alias="state"),
) -> None:
    """Exchange authorization code for user tokens (for SPA/mobile apps)"""
    if not BaseOAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseOAuthApi.subclasses[0]().google_oauth_token_exchange_api_v1_auth_oauth_google_callback_post(code, state)
