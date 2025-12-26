# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr  # noqa: F401
from typing import Any, Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401
from openapi_server.models.popular_content_response import PopularContentResponse  # noqa: F401
from openapi_server.models.user_stats_response import UserStatsResponse  # noqa: F401
from openapi_server.models.viewing_event_create import ViewingEventCreate  # noqa: F401


def test_get_popular_content_api_v1_analytics_content_popular_get(client: TestClient):
    """Test case for get_popular_content_api_v1_analytics_content_popular_get

    Get Popular Content
    """
    params = [("days", 7),     ("limit", 10)]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/analytics/content/popular",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_user_stats_api_v1_analytics_user_user_id_stats_get(client: TestClient):
    """Test case for get_user_stats_api_v1_analytics_user_user_id_stats_get

    Get User Stats
    """
    params = [("days", 30)]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/analytics/user/{user_id}/stats".format(user_id='user_id_example'),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_viewing_trends_api_v1_analytics_trends_get(client: TestClient):
    """Test case for get_viewing_trends_api_v1_analytics_trends_get

    Get Viewing Trends
    """
    params = [("days", 7)]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/analytics/trends",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_peak_hours_api_v1_analytics_peak_hours_get(client: TestClient):
    """Test case for get_peak_hours_api_v1_analytics_peak_hours_get

    Get Peak Hours
    """
    params = [("days", 7)]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/analytics/peak-hours",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_create_viewing_event_api_v1_analytics_events_post(client: TestClient):
    """Test case for create_viewing_event_api_v1_analytics_events_post

    Create Viewing Event
    """
    viewing_event_create = {"metadata":"{}","event_type":"event_type","user_id":"user_id","position_seconds":0,"session_id":"session_id","movie_id":"movie_id"}

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/analytics/events",
    #    headers=headers,
    #    json=viewing_event_create,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

