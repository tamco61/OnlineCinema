# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field  # noqa: F401
from typing import List, Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401
from openapi_server.models.watch_history_response import WatchHistoryResponse  # noqa: F401
from openapi_server.models.watch_history_update import WatchHistoryUpdate  # noqa: F401


def test_get_watch_history_api_v1_users_me_history_get(client: TestClient):
    """Test case for get_watch_history_api_v1_users_me_history_get

    Get Watch History
    """
    params = [("limit", 50)]
    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/users/me/history",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_update_watch_progress_api_v1_users_me_history_post(client: TestClient):
    """Test case for update_watch_progress_api_v1_users_me_history_post

    Update Watch Progress
    """
    watch_history_update = {"duration_seconds":0,"content_type":"content_type","content_id":"046b6c7f-0b8a-43b9-b35d-6489e6daee91","progress_seconds":0,"completed":0}

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/users/me/history",
    #    headers=headers,
    #    json=watch_history_update,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

