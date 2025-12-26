# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.health_api_base import BaseHealthApi
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
from typing import Any


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/health",
    responses={
        200: {"model": object, "description": "Successful Response"},
    },
    tags=["Health"],
    summary="Health Check",
    response_model_by_alias=True,
)
async def health_check_health_get(
) -> object:
    """Health check endpoint.  Returns service status and version."""
    if not BaseHealthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseHealthApi.subclasses[0]().health_check_health_get()
