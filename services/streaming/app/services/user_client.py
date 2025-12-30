import httpx
import logging

from app.core.config import settings
from app.services.redis import cache

logger = logging.getLogger(__name__)


class UserServiceClient:
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.timeout = settings.USER_SERVICE_TIMEOUT

    async def check_active_subscription(self, user_id: str, access_token: str) -> bool:
        cached_subscription = await cache.get_cached_subscription(user_id)

        if cached_subscription is not None:
            return cached_subscription.get("is_active", False)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/subscriptions/current",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if response.status_code == 200:
                    data = response.json()

                    subscription_data = {
                        "is_active": data.get("is_active", False),
                        "plan_id": data.get("plan_id"),
                        "expires_at": data.get("expires_at")
                    }

                    await cache.cache_subscription(user_id, subscription_data)

                    return subscription_data["is_active"]

                elif response.status_code == 404:
                    logger.warning(f"No subscription found for user: {user_id}")

                    await cache.cache_subscription(user_id, {"is_active": False})

                    return False

                else:
                    logger.error(f"Error checking subscription: {response.status_code} - {response.text}")
                    return False

        except httpx.RequestError as e:
            logger.error(f"Request error to user-service: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error checking subscription: {e}")
            return False

    async def get_user_profile(self, access_token: str) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/profiles/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if response.status_code == 200:
                    return response.json()

                return None

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None


user_service_client = UserServiceClient()


def get_user_service_client() -> UserServiceClient:
    return user_service_client
