# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.default_api_base import BaseDefaultApi
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
    "/",
    responses={
        200: {"model": object, "description": "Successful Response"},
    },
    tags=["default"],
    summary="Root",
    response_model_by_alias=True,
)
async def root_get(
) -> object:
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseDefaultApi.subclasses[0]().root_get()


@router.get(
    "/health",
    responses={
        200: {"model": object, "description": "Successful Response"},
    },
    tags=["default"],
    summary="Health",
    response_model_by_alias=True,
)
async def health_health_get(
) -> object:
    """Health check endpoint"""
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseDefaultApi.subclasses[0]().health_health_get()
