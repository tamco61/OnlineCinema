# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr  # noqa: F401
from typing import Any, List, Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from uuid import UUID  # noqa: F401
from openapi_server.models.favorite_response import FavoriteResponse  # noqa: F401
from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401


def test_get_favorites_api_v1_users_me_favorites_get(client: TestClient):
    """Test case for get_favorites_api_v1_users_me_favorites_get

    Get Favorites
    """
    params = [("limit", 100)]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/users/me/favorites",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_add_to_favorites_api_v1_users_me_favorites_content_id_post(client: TestClient):
    """Test case for add_to_favorites_api_v1_users_me_favorites_content_id_post

    Add To Favorites
    """
    params = [("content_type", 'content_type_example')]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/users/me/favorites/{content_id}".format(content_id=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_remove_from_favorites_api_v1_users_me_favorites_content_id_delete(client: TestClient):
    """Test case for remove_from_favorites_api_v1_users_me_favorites_content_id_delete

    Remove From Favorites
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "DELETE",
    #    "/api/v1/users/me/favorites/{content_id}".format(content_id=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

