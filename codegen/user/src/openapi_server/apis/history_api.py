# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.history_api_base import BaseHistoryApi
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
from pydantic import Field
from typing import List, Optional
from typing_extensions import Annotated
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.watch_history_response import WatchHistoryResponse
from openapi_server.models.watch_history_update import WatchHistoryUpdate
from openapi_server.security_api import get_token_HTTPBearer

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/v1/users/me/history",
    responses={
        200: {"model": List[WatchHistoryResponse], "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["History"],
    summary="Get Watch History",
    response_model_by_alias=True,
)
async def get_watch_history_api_v1_users_me_history_get(
    limit: Optional[Annotated[int, Field(le=100, strict=True, ge=1)]] = Query(50, description="", alias="limit", ge=1, le=100),
    token_HTTPBearer: TokenModel = Security(
        get_token_HTTPBearer
    ),
) -> List[WatchHistoryResponse]:
    """Get user watch history.  Returns recently watched content ordered by last watched time."""
    if not BaseHistoryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseHistoryApi.subclasses[0]().get_watch_history_api_v1_users_me_history_get(limit)


@router.post(
    "/api/v1/users/me/history",
    responses={
        200: {"model": WatchHistoryResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["History"],
    summary="Update Watch Progress",
    response_model_by_alias=True,
)
async def update_watch_progress_api_v1_users_me_history_post(
    watch_history_update: WatchHistoryUpdate = Body(None, description=""),
    token_HTTPBearer: TokenModel = Security(
        get_token_HTTPBearer
    ),
) -> WatchHistoryResponse:
    """Update watch progress for content.  Creates new history entry if doesn&#39;t exist, updates if exists."""
    if not BaseHistoryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseHistoryApi.subclasses[0]().update_watch_progress_api_v1_users_me_history_post(watch_history_update)
