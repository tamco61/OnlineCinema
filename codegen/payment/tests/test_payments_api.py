# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr  # noqa: F401
from typing import Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from uuid import UUID  # noqa: F401
from openapi_server.models.checkout_session_response import CheckoutSessionResponse  # noqa: F401
from openapi_server.models.create_checkout_session_request import CreateCheckoutSessionRequest  # noqa: F401
from openapi_server.models.http_validation_error import HTTPValidationError  # noqa: F401
from openapi_server.models.payment_history_response import PaymentHistoryResponse  # noqa: F401
from openapi_server.models.payment_response import PaymentResponse  # noqa: F401
from openapi_server.models.webhook_response import WebhookResponse  # noqa: F401


def test_create_checkout_session_api_v1_payments_create_checkout_session_post(client: TestClient):
    """Test case for create_checkout_session_api_v1_payments_create_checkout_session_post

    Create Checkout Session
    """
    create_checkout_session_request = {"idempotency_key":"unique-key-123","plan_id":"premium","user_id":"00000000-0000-0000-0000-000000000001"}

    headers = {
        "x_idempotency_key": 'x_idempotency_key_example',
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/payments/create-checkout-session",
    #    headers=headers,
    #    json=create_checkout_session_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_handle_webhook_api_v1_payments_webhook_post(client: TestClient):
    """Test case for handle_webhook_api_v1_payments_webhook_post

    Handle Webhook
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/api/v1/payments/webhook",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_payment_history_api_v1_payments_history_get(client: TestClient):
    """Test case for get_payment_history_api_v1_payments_history_get

    Get Payment History
    """
    params = [("user_id", UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),     ("page", 1),     ("page_size", 20)]
    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/payments/history",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_payment_api_v1_payments_payment_id_get(client: TestClient):
    """Test case for get_payment_api_v1_payments_payment_id_get

    Get Payment
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/api/v1/payments/{payment_id}".format(payment_id=UUID('38400000-8cf0-11bd-b23e-10b96e4ef00d')),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

