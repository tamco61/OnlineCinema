# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.users_api_base import BaseUsersApi
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
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.user_profile_response import UserProfileResponse
from openapi_server.models.user_profile_update import UserProfileUpdate
from openapi_server.security_api import get_token_HTTPBearer

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/v1/users/me",
    responses={
        200: {"model": UserProfileResponse, "description": "Successful Response"},
    },
    tags=["Users"],
    summary="Get My Profile",
    response_model_by_alias=True,
)
async def get_my_profile_api_v1_users_me_get(
    token_HTTPBearer: TokenModel = Security(
        get_token_HTTPBearer
    ),
) -> UserProfileResponse:
    """Get current user profile.  Creates profile automatically if doesn&#39;t exist."""
    if not BaseUsersApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUsersApi.subclasses[0]().get_my_profile_api_v1_users_me_get()


@router.patch(
    "/api/v1/users/me",
    responses={
        200: {"model": UserProfileResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Users"],
    summary="Update My Profile",
    response_model_by_alias=True,
)
async def update_my_profile_api_v1_users_me_patch(
    user_profile_update: UserProfileUpdate = Body(None, description=""),
    token_HTTPBearer: TokenModel = Security(
        get_token_HTTPBearer
    ),
) -> UserProfileResponse:
    """Update current user profile.  Updates only provided fields."""
    if not BaseUsersApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUsersApi.subclasses[0]().update_my_profile_api_v1_users_me_patch(user_profile_update)
