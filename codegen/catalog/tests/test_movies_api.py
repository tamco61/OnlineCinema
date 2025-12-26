# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr  # noqa: F401
from typing import Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from uuid import UUID  # noqa: F401
from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401
from openapi_server.models.movie_create import MovieCreate  # noqa: F401
from openapi_server.models.movie_detail_response import MovieDetailResponse  # noqa: F401
from openapi_server.models.movie_list_response import MovieListResponse  # noqa: F401
from openapi_server.models.movie_response import MovieResponse  # noqa: F401
from openapi_server.models.movie_update import MovieUpdate  # noqa: F401


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


def test_create_movie_api_v1_movies_post(client: TestClient):
    """Test case for create_movie_api_v1_movies_post

    Create Movie
    """
    movie_create = {"original_title":"original_title","year":1916,"age_rating":"age_rating","imdb_id":"imdb_id","rating":1.4658129805029452,"description":"description","poster_url":"poster_url","title":"title","genre_ids":["046b6c7f-0b8a-43b9-b35d-6489e6daee91","046b6c7f-0b8a-43b9-b35d-6489e6daee91"],"trailer_url":"trailer_url","director_ids":["046b6c7f-0b8a-43b9-b35d-6489e6daee91","046b6c7f-0b8a-43b9-b35d-6489e6daee91"],"duration":1,"actor_ids":["046b6c7f-0b8a-43b9-b35d-6489e6daee91","046b6c7f-0b8a-43b9-b35d-6489e6daee91"]}

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/movies",
    #    headers=headers,
    #    json=movie_create,
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


def test_update_movie_api_v1_movies_movie_id_patch(client: TestClient):
    """Test case for update_movie_api_v1_movies_movie_id_patch

    Update Movie
    """
    movie_update = {"duration":6,"original_title":"original_title","year":0,"age_rating":"age_rating","rating":1.4658129805029452,"description":"description","poster_url":"poster_url","title":"title","actor_ids":["046b6c7f-0b8a-43b9-b35d-6489e6daee91","046b6c7f-0b8a-43b9-b35d-6489e6daee91"],"genre_ids":["046b6c7f-0b8a-43b9-b35d-6489e6daee91","046b6c7f-0b8a-43b9-b35d-6489e6daee91"],"trailer_url":"trailer_url","director_ids":["046b6c7f-0b8a-43b9-b35d-6489e6daee91","046b6c7f-0b8a-43b9-b35d-6489e6daee91"]}

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "PATCH",
    #    "/api/v1/movies/{movie_id}".format(movie_id=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #    json=movie_update,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_publish_movie_api_v1_movies_movie_id_publish_post(client: TestClient):
    """Test case for publish_movie_api_v1_movies_movie_id_publish_post

    Publish Movie
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/movies/{movie_id}/publish".format(movie_id=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

