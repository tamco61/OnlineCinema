# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr  # noqa: F401
from typing import Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from uuid import UUID  # noqa: F401
from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401
from openapi_server.models.movie_detail_response import MovieDetailResponse  # noqa: F401
from openapi_server.models.movie_list_response import MovieListResponse  # noqa: F401


def test_get_movies_api_v1_movies_get(client: TestClient):
    """Test case for get_movies_api_v1_movies_get

    Get Movies
    """
    params = [("page", 1),     ("page_size", 20),     ("search", 'search_example')]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/movies",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_movie_api_v1_movies_movie_id_get(client: TestClient):
    """Test case for get_movie_api_v1_movies_movie_id_get

    Get Movie
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/movies/{movie_id}".format(movie_id=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

