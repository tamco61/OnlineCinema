# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.notifications_api_base import BaseNotificationsApi
import openapi_server.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from openapi_server.models.extra_models import TokenModel  # noqa: F401
from typing import Any
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.notification_response import NotificationResponse
from openapi_server.models.test_email_request import TestEmailRequest
from openapi_server.models.test_push_request import TestPushRequest


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/api/v1/notifications/test-email",
    responses={
        200: {"model": NotificationResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Notifications"],
    summary="Send Test Email",
    response_model_by_alias=True,
)
async def send_test_email_api_v1_notifications_test_email_post(
    test_email_request: TestEmailRequest = Body(None, description=""),
) -> NotificationResponse:
    """Send test email  **Admin endpoint** for testing email provider configuration  **Request:** &#x60;&#x60;&#x60;json {     \&quot;to_email\&quot;: \&quot;user@example.com\&quot;,     \&quot;to_name\&quot;: \&quot;John Doe\&quot;,     \&quot;subject\&quot;: \&quot;Test Email\&quot;,     \&quot;body\&quot;: \&quot;&lt;h1&gt;Hello!&lt;/h1&gt;&lt;p&gt;This is a test.&lt;/p&gt;\&quot; } &#x60;&#x60;&#x60;  **Response:** &#x60;&#x60;&#x60;json {     \&quot;success\&quot;: true,     \&quot;message\&quot;: \&quot;Email sent successfully\&quot;,     \&quot;message_id\&quot;: \&quot;msg-12345\&quot; } &#x60;&#x60;&#x60;  **Example:** &#x60;&#x60;&#x60;bash curl -X POST http://localhost:8008/api/v1/notifications/test-email \\   -H \&quot;Content-Type: application/json\&quot; \\   -d &#39;{     \&quot;to_email\&quot;: \&quot;user@example.com\&quot;,     \&quot;subject\&quot;: \&quot;Test\&quot;,     \&quot;body\&quot;: \&quot;&lt;h1&gt;Test Email&lt;/h1&gt;\&quot;   }&#39; &#x60;&#x60;&#x60;"""
    if not BaseNotificationsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseNotificationsApi.subclasses[0]().send_test_email_api_v1_notifications_test_email_post(test_email_request)


@router.post(
    "/api/v1/notifications/test-push",
    responses={
        200: {"model": NotificationResponse, "description": "Successful Response"},
        422: {"model": HTTPValidationError, "description": "Validation Error"},
    },
    tags=["Notifications"],
    summary="Send Test Push",
    response_model_by_alias=True,
)
async def send_test_push_api_v1_notifications_test_push_post(
    test_push_request: TestPushRequest = Body(None, description=""),
) -> NotificationResponse:
    """Send test push notification  **Admin endpoint** for testing push provider configuration  **Request:** &#x60;&#x60;&#x60;json {     \&quot;device_token\&quot;: \&quot;fcm-token\&quot;,     \&quot;title\&quot;: \&quot;Test Notification\&quot;,     \&quot;body\&quot;: \&quot;This is a test\&quot;,     \&quot;data\&quot;: {\&quot;key\&quot;: \&quot;value\&quot;} } &#x60;&#x60;&#x60;  **Response:** &#x60;&#x60;&#x60;json {     \&quot;success\&quot;: true,     \&quot;message\&quot;: \&quot;Push notification sent successfully\&quot;,     \&quot;message_id\&quot;: \&quot;fcm-12345\&quot; } &#x60;&#x60;&#x60;  **Example:** &#x60;&#x60;&#x60;bash curl -X POST http://localhost:8008/api/v1/notifications/test-push \\   -H \&quot;Content-Type: application/json\&quot; \\   -d &#39;{     \&quot;device_token\&quot;: \&quot;your-fcm-token\&quot;,     \&quot;title\&quot;: \&quot;Test\&quot;,     \&quot;body\&quot;: \&quot;Test push\&quot;   }&#39; &#x60;&#x60;&#x60;"""
    if not BaseNotificationsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseNotificationsApi.subclasses[0]().send_test_push_api_v1_notifications_test_push_post(test_push_request)


@router.get(
    "/api/v1/notifications/providers",
    responses={
        200: {"model": object, "description": "Successful Response"},
    },
    tags=["Notifications"],
    summary="Get Providers",
    response_model_by_alias=True,
)
async def get_providers_api_v1_notifications_providers_get(
) -> object:
    """Get configured notification providers  **Returns:** Information about configured email and push providers  **Example:** &#x60;&#x60;&#x60;bash curl http://localhost:8008/api/v1/notifications/providers &#x60;&#x60;&#x60;"""
    if not BaseNotificationsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseNotificationsApi.subclasses[0]().get_providers_api_v1_notifications_providers_get()
