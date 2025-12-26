# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictStr
from typing import Optional
from typing_extensions import Annotated
from uuid import UUID
from openapi_server.models.checkout_session_response import CheckoutSessionResponse
from openapi_server.models.create_checkout_session_request import CreateCheckoutSessionRequest
from openapi_server.models.http_validation_error import HTTPValidationError
from openapi_server.models.payment_history_response import PaymentHistoryResponse
from openapi_server.models.payment_response import PaymentResponse
from openapi_server.models.webhook_response import WebhookResponse


class BasePaymentsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BasePaymentsApi.subclasses = BasePaymentsApi.subclasses + (cls,)
    async def create_checkout_session_api_v1_payments_create_checkout_session_post(
        self,
        create_checkout_session_request: CreateCheckoutSessionRequest,
        x_idempotency_key: Optional[StrictStr],
    ) -> CheckoutSessionResponse:
        """Create checkout session for subscription payment  **Idempotency:** - Use &#x60;X-Idempotency-Key&#x60; header or &#x60;idempotency_key&#x60; field - Prevents duplicate payments if request is retried - Cached for 24 hours  **Request:** &#x60;&#x60;&#x60;json {     \&quot;plan_id\&quot;: \&quot;premium\&quot;,     \&quot;user_id\&quot;: \&quot;00000000-0000-0000-0000-000000000001\&quot;,     \&quot;idempotency_key\&quot;: \&quot;optional-unique-key\&quot; } &#x60;&#x60;&#x60;  **Response:** &#x60;&#x60;&#x60;json {     \&quot;payment_id\&quot;: \&quot;uuid\&quot;,     \&quot;checkout_url\&quot;: \&quot;https://yookassa.ru/checkout/...\&quot;,     \&quot;amount\&quot;: 599.00,     \&quot;currency\&quot;: \&quot;RUB\&quot;,     \&quot;plan_id\&quot;: \&quot;premium\&quot; } &#x60;&#x60;&#x60;  **Example:** &#x60;&#x60;&#x60;bash curl -X POST http://localhost:8007/api/v1/payments/create-checkout-session \\   -H \&quot;Content-Type: application/json\&quot; \\   -H \&quot;X-Idempotency-Key: unique-key-123\&quot; \\   -d &#39;{     \&quot;plan_id\&quot;: \&quot;premium\&quot;,     \&quot;user_id\&quot;: \&quot;00000000-0000-0000-0000-000000000001\&quot;   }&#39; &#x60;&#x60;&#x60;"""
        ...


    async def handle_webhook_api_v1_payments_webhook_post(
        self,
    ) -> WebhookResponse:
        """YooMoney webhook handler  **Supported Events:** - &#x60;payment.succeeded&#x60; - Payment completed successfully - &#x60;payment.canceled&#x60; - Payment cancelled by user or timeout - &#x60;refund.succeeded&#x60; - Refund processed  **Webhook Configuration:** Set webhook URL in YooMoney dashboard: &#x60;&#x60;&#x60; https://your-domain.com/api/v1/payments/webhook &#x60;&#x60;&#x60;  **Security:** - Webhook signature verification using HMAC-SHA256 - Set &#x60;YOOMONEY_WEBHOOK_SECRET&#x60; in environment  **Example Webhook Payload:** &#x60;&#x60;&#x60;json {     \&quot;type\&quot;: \&quot;notification\&quot;,     \&quot;event\&quot;: \&quot;payment.succeeded\&quot;,     \&quot;object\&quot;: {         \&quot;id\&quot;: \&quot;2d8b8b7a-000f-5000-9000-1b7e3f9e0e9f\&quot;,         \&quot;status\&quot;: \&quot;succeeded\&quot;,         \&quot;paid\&quot;: true,         \&quot;amount\&quot;: {             \&quot;value\&quot;: \&quot;599.00\&quot;,             \&quot;currency\&quot;: \&quot;RUB\&quot;         },         \&quot;payment_metadata\&quot;: {             \&quot;payment_id\&quot;: \&quot;uuid\&quot;         }     } } &#x60;&#x60;&#x60;  **Testing:** &#x60;&#x60;&#x60;bash curl -X POST http://localhost:8007/api/v1/payments/webhook \\   -H \&quot;Content-Type: application/json\&quot; \\   -H \&quot;X-YooKassa-Signature: signature\&quot; \\   -d &#39;{     \&quot;type\&quot;: \&quot;notification\&quot;,     \&quot;event\&quot;: \&quot;payment.succeeded\&quot;,     \&quot;object\&quot;: {         \&quot;id\&quot;: \&quot;provider-payment-id\&quot;,         \&quot;status\&quot;: \&quot;succeeded\&quot;     }   }&#39; &#x60;&#x60;&#x60;"""
        ...


    async def get_payment_history_api_v1_payments_history_get(
        self,
        user_id: Annotated[UUID, Field(description="User UUID")],
        page: Annotated[Optional[Annotated[int, Field(strict=True, ge=1)]], Field(description="Page number")],
        page_size: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Items per page")],
    ) -> PaymentHistoryResponse:
        """Get payment history for user  **Query Parameters:** - &#x60;user_id&#x60; - User UUID (required) - &#x60;page&#x60; - Page number (default: 1) - &#x60;page_size&#x60; - Items per page (default: 20, max: 100)  **Response:** &#x60;&#x60;&#x60;json {     \&quot;payments\&quot;: [         {             \&quot;id\&quot;: \&quot;uuid\&quot;,             \&quot;user_id\&quot;: \&quot;uuid\&quot;,             \&quot;amount\&quot;: 599.00,             \&quot;currency\&quot;: \&quot;RUB\&quot;,             \&quot;status\&quot;: \&quot;succeeded\&quot;,             \&quot;provider\&quot;: \&quot;yoomoney\&quot;,             \&quot;plan_id\&quot;: \&quot;premium\&quot;,             \&quot;created_at\&quot;: \&quot;2024-11-16T10:00:00Z\&quot;         }     ],     \&quot;total\&quot;: 10,     \&quot;page\&quot;: 1,     \&quot;page_size\&quot;: 20 } &#x60;&#x60;&#x60;  **Example:** &#x60;&#x60;&#x60;bash curl \&quot;http://localhost:8007/api/v1/payments/history?user_id&#x3D;{uuid}&amp;page&#x3D;1&amp;page_size&#x3D;20\&quot; &#x60;&#x60;&#x60;"""
        ...


    async def get_payment_api_v1_payments_payment_id_get(
        self,
        payment_id: UUID,
    ) -> PaymentResponse:
        """Get payment details by ID  **Example:** &#x60;&#x60;&#x60;bash curl \&quot;http://localhost:8007/api/v1/payments/{payment_id}\&quot; &#x60;&#x60;&#x60;"""
        ...
