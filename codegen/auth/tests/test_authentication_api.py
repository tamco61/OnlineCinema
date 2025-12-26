# coding: utf-8

from fastapi.testclient import TestClient


from openapi_server.models.auth_response import AuthResponse  # noqa: F401
from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401
from openapi_server.models.logout_request import LogoutRequest  # noqa: F401
from openapi_server.models.message_response import MessageResponse  # noqa: F401
from openapi_server.models.token_refresh import TokenRefresh  # noqa: F401
from openapi_server.models.token_response import TokenResponse  # noqa: F401
from openapi_server.models.user_login import UserLogin  # noqa: F401
from openapi_server.models.user_register import UserRegister  # noqa: F401
from openapi_server.models.user_response import UserResponse  # noqa: F401


def test_register_api_v1_auth_register_post(client: TestClient):
    """Test case for register_api_v1_auth_register_post

    Register new user
    """
    user_register = {"password":"password","email":"email"}

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/auth/register",
    #    headers=headers,
    #    json=user_register,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_login_api_v1_auth_login_post(client: TestClient):
    """Test case for login_api_v1_auth_login_post

    Login user
    """
    user_login = {"password":"password","email":"email"}

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/auth/login",
    #    headers=headers,
    #    json=user_login,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_refresh_token_api_v1_auth_refresh_post(client: TestClient):
    """Test case for refresh_token_api_v1_auth_refresh_post

    Refresh access token
    """
    token_refresh = {"refresh_token":"refresh_token"}

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/auth/refresh",
    #    headers=headers,
    #    json=token_refresh,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_logout_api_v1_auth_logout_post(client: TestClient):
    """Test case for logout_api_v1_auth_logout_post

    Logout user
    """
    logout_request = {"refresh_token":"refresh_token"}

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/auth/logout",
    #    headers=headers,
    #    json=logout_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_logout_all_api_v1_auth_logout_all_post(client: TestClient):
    """Test case for logout_all_api_v1_auth_logout_all_post

    Logout from all devices
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/auth/logout-all",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_current_user_info_api_v1_auth_me_get(client: TestClient):
    """Test case for get_current_user_info_api_v1_auth_me_get

    Get current user info
    """

    headers = {
        "Authorization": "Bearer special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/auth/me",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

