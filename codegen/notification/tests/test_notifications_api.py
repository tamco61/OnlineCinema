# coding: utf-8

from fastapi.testclient import TestClient


from typing import Any  # noqa: F401
from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401
from openapi_server.models.notification_response import NotificationResponse  # noqa: F401
from openapi_server.models.test_email_request import TestEmailRequest  # noqa: F401
from openapi_server.models.test_push_request import TestPushRequest  # noqa: F401


def test_send_test_email_api_v1_notifications_test_email_post(client: TestClient):
    """Test case for send_test_email_api_v1_notifications_test_email_post

    Send Test Email
    """
    test_email_request = {"body":"<h1>Hello!</h1><p>This is a test email.</p>","subject":"Test Email","to_email":"user@example.com","to_name":"John Doe"}

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/notifications/test-email",
    #    headers=headers,
    #    json=test_email_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_send_test_push_api_v1_notifications_test_push_post(client: TestClient):
    """Test case for send_test_push_api_v1_notifications_test_push_post

    Send Test Push
    """
    test_push_request = {"body":"This is a test push notification","data":{"key":"value","type":"test"},"device_token":"fcm-device-token-here","title":"Test Notification"}

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/notifications/test-push",
    #    headers=headers,
    #    json=test_push_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_providers_api_v1_notifications_providers_get(client: TestClient):
    """Test case for get_providers_api_v1_notifications_providers_get

    Get Providers
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/notifications/providers",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

