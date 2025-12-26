# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictBool, StrictStr  # noqa: F401
from typing import Any, Optional, Union  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401
from openapi_server.models.search_response import SearchResponse  # noqa: F401
from openapi_server.models.suggest_response import SuggestResponse  # noqa: F401


def test_search_movies_api_v1_search_get(client: TestClient):
    """Test case for search_movies_api_v1_search_get

    Search Movies
    """
    params = [("query", 'query_example'),     ("genres", 'genres_example'),     ("year_from", 56),     ("year_to", 56),     ("rating_from", 3.4),     ("rating_to", 3.4),     ("age_rating", 'age_rating_example'),     ("page", 1),     ("size", 20),     ("published_only", True)]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/search",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_autocomplete_movies_api_v1_search_suggest_get(client: TestClient):
    """Test case for autocomplete_movies_api_v1_search_suggest_get

    Autocomplete Movies
    """
    params = [("query", 'query_example'),     ("limit", 10)]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/search/suggest",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_health_check_api_v1_search_health_get(client: TestClient):
    """Test case for health_check_api_v1_search_health_get

    Health Check
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/search/health",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

