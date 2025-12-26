# coding: utf-8

from fastapi.testclient import TestClient


from typing import Any  # noqa: F401


def test_root_get(client: TestClient):
    """Test case for root_get

    Root
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

