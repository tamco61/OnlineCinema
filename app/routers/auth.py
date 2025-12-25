"""
Роутер аутентификации и авторизации
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import datetime, timedelta
from typing import Optional
import secrets
import logging

from config import settings
from database import get_session
import dependencies
import models
import schemas

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=schemas.UserResponse)
async def register(
        user_data: schemas.UserCreate,
        background_tasks: BackgroundTasks,
        session: Session = Depends(get_session)
):
    """
    Регистрация нового пользователя
    """
    # Проверка существующего email
    existing_email = dependencies.get_user_by_email(user_data.email, session)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    # Проверка существующего username
    existing_username = dependencies.get_user_by_username(user_data.username, session)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует"
        )

    # Хеширование пароля
    hashed_password = dependencies.get_password_hash(user_data.password)

    # Создание пользователя
    db_user = models.User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        subscription_tier_id=settings.default_subscription_tier_id
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    logger.info(f"Новый пользователь зарегистрирован: {db_user.email}")

    # Отправка email верификации (в фоне)
    # background_tasks.add_task(send_verification_email, db_user.email)

    return db_user


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: Session = Depends(get_session)
):
    """
    Вход в систему и получение токена
    """
    # Аутентификация пользователя
    user = dependencies.authenticate_user(
        form_data.username,
        form_data.password,
        session
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Обновляем время последнего входа
    user.last_login = datetime.utcnow()
    session.add(user)
    session.commit()

    # Создаем access токен
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = dependencies.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    # Создаем refresh токен (если нужно запомнить пользователя)
    refresh_token = None
    if form_data.get("remember_me", False):
        refresh_token = dependencies.create_refresh_token(user.id)

    logger.info(f"Пользователь вошел в систему: {user.email}")

    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        refresh_token=refresh_token,
        user=user
    )


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(
        refresh_request: schemas.RefreshTokenRequest,
        session: Session = Depends(get_session)
):
    """
    Обновление access токена с помощью refresh токена
    """
    payload = dependencies.decode_token(refresh_request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный refresh токен"
        )

    user_id = int(payload.get("sub"))
    user = session.get(models.User, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или неактивен"
        )

    # Создаем новый access токен
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = dependencies.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        user=user
    )


@router.post("/logout")
async def logout(
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Выход из системы
    """
    # В реальном приложении здесь можно:
    # 1. Добавить токен в черный список
    # 2. Удалить refresh токен из БД
    # 3. Очистить сессию

    logger.info(f"Пользователь вышел из системы: {current_user.email}")

    return schemas.SuccessResponse(
        message="Успешный выход из системы"
    )


@router.post("/password/reset")
async def reset_password_request(
        reset_request: schemas.PasswordResetRequest,
        background_tasks: BackgroundTasks,
        session: Session = Depends(get_session)
):
    """
    Запрос на сброс пароля
    """
    user = dependencies.get_user_by_email(reset_request.email, session)

    if user:
        # Генерация токена сброса пароля
        reset_token = secrets.token_urlsafe(32)

        # Сохранение токена в БД (в реальном приложении)
        # user.reset_token = reset_token
        # user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        # session.add(user)
        # session.commit()

        # Отправка email (в фоне)
        # background_tasks.add_task(send_password_reset_email, user.email, reset_token)

        logger.info(f"Запрос сброса пароля для: {user.email}")

    # Всегда возвращаем успех, даже если пользователь не найден
    # (для безопасности не раскрываем информацию о существовании email)
    return schemas.SuccessResponse(
        message="Если email зарегистрирован, инструкции отправлены"
    )


@router.post("/password/reset/confirm")
async def reset_password_confirm(
        reset_data: schemas.PasswordResetConfirm,
        session: Session = Depends(get_session)
):
    """
    Подтверждение сброса пароля
    """
    # В реальном приложении:
    # 1. Проверяем токен и его срок действия
    # 2. Находим пользователя по токену
    # 3. Обновляем пароль

    # Здесь упрощенная реализация
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Функция в разработке"
    )


@router.post("/email/verify")
async def verify_email(
        verify_request: schemas.EmailVerificationRequest,
        session: Session = Depends(get_session)
):
    """
    Подтверждение email
    """
    # В реальном приложении:
    # 1. Проверяем токен верификации
    # 2. Находим пользователя
    # 3. Обновляем статус верификации

    # Здесь упрощенная реализация
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Функция в разработке"
    )


@router.post("/email/resend-verification")
async def resend_verification_email(
        current_user: models.User = Depends(dependencies.get_current_user),
        background_tasks: BackgroundTasks = None
):
    """
    Повторная отправка email верификации
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже подтвержден"
        )

    # Отправка email (в фоне)
    # if background_tasks:
    #     background_tasks.add_task(send_verification_email, current_user.email)

    return schemas.SuccessResponse(
        message="Письмо с подтверждением отправлено"
    )


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Получение информации о текущем пользователе
    """
    return current_user


# Вспомогательные функции для email
async def send_verification_email(email: str):
    """
    Отправка email верификации
    """
    # Реализация отправки email
    logger.info(f"Отправка email верификации на: {email}")


async def send_password_reset_email(email: str, token: str):
    """
    Отправка email сброса пароля
    """
    # Реализация отправки email
    logger.info(f"Отправка email сброса пароля на: {email}")