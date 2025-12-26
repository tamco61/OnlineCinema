# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import StrictStr  # noqa: F401
from typing import Any  # noqa: F401
from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401
from openapi_server.models.progress_update_request import ProgressUpdateRequest  # noqa: F401
from openapi_server.models.progress_update_response import ProgressUpdateResponse  # noqa: F401
from openapi_server.models.stream_request import StreamRequest  # noqa: F401
from openapi_server.models.stream_response import StreamResponse  # noqa: F401
from openapi_server.models.watch_progress_response import WatchProgressResponse  # noqa: F401


def test_start_streaming_api_v1_stream_movie_id_post(client: TestClient):
    """Test case for start_streaming_api_v1_stream_movie_id_post

    Start Streaming
    """
    stream_request = {"manifest_type":"hls"}

    headers = {
        "authorization": 'authorization_example',
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/stream/{movie_id}".format(movie_id='movie_id_example'),
    #    headers=headers,
    #    json=stream_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_watch_progress_api_v1_stream_movie_id_progress_get(client: TestClient):
    """Test case for get_watch_progress_api_v1_stream_movie_id_progress_get

    Get Watch Progress
    """

    headers = {
        "authorization": 'authorization_example',
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/stream/{movie_id}/progress".format(movie_id='movie_id_example'),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_update_watch_progress_api_v1_stream_movie_id_progress_post(client: TestClient):
    """Test case for update_watch_progress_api_v1_stream_movie_id_progress_post

    Update Watch Progress
    """
    progress_update_request = {"position_seconds":0}

    headers = {
        "authorization": 'authorization_example',
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/stream/{movie_id}/progress".format(movie_id='movie_id_example'),
    #    headers=headers,
    #    json=progress_update_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_stop_streaming_api_v1_stream_movie_id_stop_post(client: TestClient):
    """Test case for stop_streaming_api_v1_stream_movie_id_stop_post

    Stop Streaming
    """
    progress_update_request = {"position_seconds":0}

    headers = {
        "authorization": 'authorization_example',
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/stream/{movie_id}/stop".format(movie_id='movie_id_example'),
    #    headers=headers,
    #    json=progress_update_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

