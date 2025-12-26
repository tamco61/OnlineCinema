# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.authentication_api_base import BaseAuthenticationApi
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

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/api/v1/auth/register",
    responses={
        201: {"model": AuthResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Authentication"],
    summary="Register new user",
    response_model_by_alias=True,
)
async def register_api_v1_auth_register_post(
    user_register: UserRegister = Body(None, description=""),
) -> AuthResponse:
    """Create a new user account with email and password"""
    if not BaseAuthenticationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthenticationApi.subclasses[0]().register_api_v1_auth_register_post(user_register)


@router.post(
    "/api/v1/auth/login",
    responses={
        200: {"model": AuthResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Authentication"],
    summary="Login user",
    response_model_by_alias=True,
)
async def login_api_v1_auth_login_post(
    user_login: UserLogin = Body(None, description=""),
) -> AuthResponse:
    """Authenticate user and receive access and refresh tokens"""
    if not BaseAuthenticationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthenticationApi.subclasses[0]().login_api_v1_auth_login_post(user_login)


@router.post(
    "/api/v1/auth/refresh",
    responses={
        200: {"model": TokenResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Authentication"],
    summary="Refresh access token",
    response_model_by_alias=True,
)
async def refresh_token_api_v1_auth_refresh_post(
    token_refresh: TokenRefresh = Body(None, description=""),
) -> TokenResponse:
    """Get a new access token using a valid refresh token"""
    if not BaseAuthenticationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthenticationApi.subclasses[0]().refresh_token_api_v1_auth_refresh_post(token_refresh)


@router.post(
    "/api/v1/auth/logout",
    responses={
        200: {"model": MessageResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Authentication"],
    summary="Logout user",
    response_model_by_alias=True,
)
async def logout_api_v1_auth_logout_post(
    logout_request: LogoutRequest = Body(None, description=""),
) -> MessageResponse:
    """Invalidate refresh token (logout from current device)"""
    if not BaseAuthenticationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthenticationApi.subclasses[0]().logout_api_v1_auth_logout_post(logout_request)


@router.post(
    "/api/v1/auth/logout-all",
    responses={
        200: {"model": MessageResponse, "description": "Successful Response"},
    },
    tags=["Authentication"],
    summary="Logout from all devices",
    response_model_by_alias=True,
)
async def logout_all_api_v1_auth_logout_all_post(
    token_HTTPBearer: TokenModel = Security(
        get_token_HTTPBearer
    ),
) -> MessageResponse:
    """Invalidate all refresh tokens for the authenticated user"""
    if not BaseAuthenticationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthenticationApi.subclasses[0]().logout_all_api_v1_auth_logout_all_post()


@router.get(
    "/api/v1/auth/me",
    responses={
        200: {"model": UserResponse, "description": "Successful Response"},
    },
    tags=["Authentication"],
    summary="Get current user info",
    response_model_by_alias=True,
)
async def get_current_user_info_api_v1_auth_me_get(
    token_HTTPBearer: TokenModel = Security(
        get_token_HTTPBearer
    ),
) -> UserResponse:
    """Get information about the authenticated user"""
    if not BaseAuthenticationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthenticationApi.subclasses[0]().get_current_user_info_api_v1_auth_me_get()
