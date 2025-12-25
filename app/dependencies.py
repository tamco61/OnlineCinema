"""
Зависимости и утилиты для FastAPI
"""

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from sqlmodel import Session, select
from typing import Optional, Generator, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
import logging

from config import settings
from database import get_session
import models
import schemas

logger = logging.getLogger(__name__)

# ============ НАСТРОЙКИ БЕЗОПАСНОСТИ ============

# OAuth2 для паролей
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_prefix}/auth/login",
    auto_error=False
)

# HTTP Bearer для токенов
bearer_scheme = HTTPBearer(auto_error=False)

# Контекст для хеширования паролей
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


# ============ УТИЛИТЫ ДЛЯ РАБОТЫ С ПАРОЛЯМИ ============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Получение хеша пароля"""
    return pwd_context.hash(password)


def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
) -> str:
    """
    Создание JWT токена

    Args:
        data: Данные для включения в токен
        expires_delta: Время жизни токена

    Returns:
        JWT токен
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(
        user_id: int,
        expires_delta: Optional[timedelta] = None
) -> str:
    """
    Создание refresh токена

    Args:
        user_id: ID пользователя
        expires_delta: Время жизни токена

    Returns:
        Refresh токен
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)

    to_encode = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + expires_delta,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Декодирование JWT токена

    Args:
        token: JWT токен

    Returns:
        Декодированные данные или None
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except ExpiredSignatureError:
        logger.warning("Токен истек")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.warning(f"Ошибка декодирования токена: {e}")
        return None


# ============ ЗАВИСИМОСТИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ============

def get_current_user(
        token: Optional[str] = Depends(oauth2_scheme),
        session: Session = Depends(get_session)
) -> models.User:
    """
    Получение текущего пользователя из токена

    Args:
        token: JWT токен
        session: Сессия БД

    Returns:
        Модель пользователя

    Raises:
        HTTPException: Если токен невалидный или пользователь не найден
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")

    if user_id is None or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный формат токена",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.get(models.User, user_id_int)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован"
        )

    return user


def get_current_active_user(
        current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Получение активного пользователя

    Args:
        current_user: Текущий пользователь

    Returns:
        Активный пользователь

    Raises:
        HTTPException: Если пользователь неактивен
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь неактивен"
        )
    return current_user


def get_current_verified_user(
        current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Получение верифицированного пользователя

    Args:
        current_user: Текущий пользователь

    Returns:
        Верифицированный пользователь

    Raises:
        HTTPException: Если email не подтвержден
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email не подтвержден"
        )
    return current_user


def get_current_staff_user(
        current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Получение пользователя с правами staff

    Args:
        current_user: Текущий пользователь

    Returns:
        Пользователь staff

    Raises:
        HTTPException: Если недостаточно прав
    """
    if not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return current_user


def get_current_superuser(
        current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Получение суперпользователя

    Args:
        current_user: Текущий пользователь

    Returns:
        Суперпользователь

    Raises:
        HTTPException: Если недостаточно прав
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права суперпользователя"
        )
    return current_user


# ============ ЗАВИСИМОСТИ ДЛЯ ПРОВЕРКИ ПРАВ ============

def check_subscription_tier(
        required_tier: str,
        current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Проверка уровня подписки пользователя

    Args:
        required_tier: Требуемый уровень подписки (free, basic, premium, family)
        current_user: Текущий пользователь

    Returns:
        Пользователь с достаточным уровнем подписки

    Raises:
        HTTPException: Если подписка недостаточна
    """
    tier_order = {"free": 0, "basic": 1, "premium": 2, "family": 3}

    user_tier = current_user.subscription_tier_rel.code
    required_tier_order = tier_order.get(required_tier, 0)
    user_tier_order = tier_order.get(user_tier, 0)

    if user_tier_order < required_tier_order:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Требуется подписка уровня {required_tier} или выше"
        )

    return current_user


def check_content_access(
        content: models.Content,
        current_user: models.User = Depends(get_current_user)
) -> models.Content:
    """
    Проверка доступа пользователя к контенту

    Args:
        content: Контент для проверки
        current_user: Текущий пользователь

    Returns:
        Контент, если доступ разрешен

    Raises:
        HTTPException: Если доступ запрещен
    """
    # Проверка возрастного рейтинга
    if content.age_rating_rel.min_age is not None:
        # Здесь можно добавить логику проверки возраста пользователя
        pass

    # Проверка подписки
    if content.requires_subscription:
        if current_user.subscription_tier_rel.code == "free":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуется подписка для доступа к этому контенту"
            )

    # Проверка доступности
    if not content.is_available:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контент временно недоступен"
        )

    now = datetime.utcnow()
    if content.available_to and content.available_to < now:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Срок действия контента истек"
        )

    if content.available_from > now:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контент будет доступен позже"
        )

    return content


# ============ УТИЛИТЫ ДЛЯ РАБОТЫ С БД ============

def get_db() -> Generator[Session, None, None]:
    """
    Генератор сессий БД

    Использование:
    ```python
    db = next(get_db())
    ```
    """
    with get_session() as session:
        yield session


def get_user_by_email(email: str, session: Session) -> Optional[models.User]:
    """Получение пользователя по email"""
    return session.exec(
        select(models.User).where(models.User.email == email)
    ).first()


def get_user_by_username(username: str, session: Session) -> Optional[models.User]:
    """Получение пользователя по имени пользователя"""
    return session.exec(
        select(models.User).where(models.User.username == username)
    ).first()


def authenticate_user(
        username: str,
        password: str,
        session: Session
) -> Optional[models.User]:
    """
    Аутентификация пользователя

    Args:
        username: Имя пользователя или email
        password: Пароль
        session: Сессия БД

    Returns:
        Пользователь или None
    """
    # Пробуем найти по email
    user = get_user_by_email(username, session)

    # Если не нашли по email, ищем по username
    if not user:
        user = get_user_by_username(username, session)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


# ============ ДЕКОРАТОРЫ ДЛЯ ПРОВЕРКИ ПРАВ ============

from functools import wraps
from typing import Callable, Any


def require_permission(permission: str):
    """
    Декоратор для проверки прав доступа

    Args:
        permission: Требуемое право

    Пример:
    ```python
    @require_permission("content.create")
    def create_content(...):
        ...
    ```
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Здесь можно реализовать проверку прав
            # Пока что просто пропускаем
            return func(*args, **kwargs)

        return wrapper

    return decorator


def rate_limit(requests_per_minute: int = 60):
    """
    Декоратор для ограничения запросов

    Args:
        requests_per_minute: Максимальное количество запросов в минуту

    Пример:
    ```python
    @rate_limit(30)
    def expensive_operation(...):
        ...
    ```
    """
    from fastapi import Request
    import time

    requests = {}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            current_time = time.time()

            # Очистка старых записей
            requests[client_ip] = [
                req_time for req_time in requests.get(client_ip, [])
                if current_time - req_time < 60
            ]

            # Проверка лимита
            if len(requests.get(client_ip, [])) >= requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Слишком много запросов"
                )

            # Добавление нового запроса
            requests.setdefault(client_ip, []).append(current_time)

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


# ============ ВАЛИДАЦИЯ ============

def validate_pagination_params(
        page: int = 1,
        size: int = 20,
        max_size: int = 100
) -> schemas.PaginationParams:
    """
    Валидация параметров пагинации

    Args:
        page: Номер страницы
        size: Размер страницы
        max_size: Максимальный размер страницы

    Returns:
        Валидированные параметры пагинации
    """
    if page < 1:
        page = 1

    if size < 1:
        size = 20
    elif size > max_size:
        size = max_size

    return schemas.PaginationParams(page=page, size=size)


# Экспортируемые зависимости
CurrentUser = Depends(get_current_user)
CurrentActiveUser = Depends(get_current_active_user)
CurrentVerifiedUser = Depends(get_current_verified_user)
CurrentStaffUser = Depends(get_current_staff_user)
CurrentSuperuser = Depends(get_current_superuser)
DB = Depends(get_db)