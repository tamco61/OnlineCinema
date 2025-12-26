# coding: utf-8

from fastapi.testclient import TestClient


from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401
from openapi_server.models.user_profile_response import UserProfileResponse  # noqa: F401
from openapi_server.models.user_profile_update import UserProfileUpdate  # noqa: F401


def test_get_my_profile_api_v1_users_me_get(client: TestClient):
    """Test case for get_my_profile_api_v1_users_me_get

    Get My Profile
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/users/me",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_update_my_profile_api_v1_users_me_patch(client: TestClient):
    """Test case for update_my_profile_api_v1_users_me_patch

    Update My Profile
    """
    user_profile_update = {"country":"country","avatar_url":"avatar_url","nickname":"nickname","language":"language"}

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "PATCH",
    #    "/api/v1/users/me",
    #    headers=headers,
    #    json=user_profile_update,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

