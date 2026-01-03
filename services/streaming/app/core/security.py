import logging
import uuid
import jwt
from datetime import datetime
from services.streaming.app.core.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)


def verify_access_token(token: str) -> uuid.UUID | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("type") != "access":
            logger.warning("Invalid token type")
            return None

        exp = payload.get("exp")
        if exp and datetime.now().timestamp() > exp:
            logger.warning("Token expired")
            return None

        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Missing user_id in token")
            return None

        return uuid.UUID(user_id)

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except ValueError as e:
        logger.warning(f"Invalid user_id format: {e}")
        return None
