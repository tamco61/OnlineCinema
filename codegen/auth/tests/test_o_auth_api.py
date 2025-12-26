# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr  # noqa: F401
from typing import Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401
from openapi_server.models.message_response import MessageResponse  # noqa: F401
from openapi_server.models.o_auth_authorization_response import OAuthAuthorizationResponse  # noqa: F401
from openapi_server.models.o_auth_callback_response import OAuthCallbackResponse  # noqa: F401


def test_google_oauth_init_api_v1_auth_oauth_google_get(client: TestClient):
    """Test case for google_oauth_init_api_v1_auth_oauth_google_get

    Initiate Google OAuth
    """
    params = [("redirect_uri", 'redirect_uri_example')]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/auth/oauth/google",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_google_oauth_callback_api_v1_auth_oauth_google_callback_get(client: TestClient):
    """Test case for google_oauth_callback_api_v1_auth_oauth_google_callback_get

    Google OAuth callback
    """
    params = [("code", 'code_example'),     ("state", 'state_example')]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/auth/oauth/google/callback",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_google_oauth_token_exchange_api_v1_auth_oauth_google_callback_post(client: TestClient):
    """Test case for google_oauth_token_exchange_api_v1_auth_oauth_google_callback_post

    Process Google OAuth code
    """
    params = [("code", 'code_example'),     ("state", 'state_example')]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/auth/oauth/google/callback",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

