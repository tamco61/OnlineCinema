"""
Роутер пользователей
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from database import get_session
import dependencies
import models
import schemas

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user(
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Получение информации о текущем пользователе
    """
    return current_user


@router.put("/me", response_model=schemas.UserResponse)
async def update_current_user(
        user_update: schemas.UserUpdate,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Обновление информации текущего пользователя
    """
    update_data = user_update.dict(exclude_unset=True)

    # Проверка уникальности email
    if "email" in update_data and update_data["email"] != current_user.email:
        existing = dependencies.get_user_by_email(update_data["email"], session)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже используется"
            )

    # Проверка уникальности username
    if "username" in update_data and update_data["username"] != current_user.username:
        existing = dependencies.get_user_by_username(update_data["username"], session)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Имя пользователя уже используется"
            )

    # Обновляем поля
    for key, value in update_data.items():
        setattr(current_user, key, value)

    current_user.updated_at = datetime.utcnow()
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    logger.info(f"Пользователь обновлен: {current_user.email}")
    return current_user


@router.patch("/me/profile", response_model=schemas.UserResponse)
async def update_profile(
        profile_update: schemas.UserProfileUpdate,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Обновление профиля пользователя
    """
    update_data = profile_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(current_user, key, value)

    current_user.updated_at = datetime.utcnow()
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user


@router.post("/me/password", response_model=schemas.SuccessResponse)
async def change_password(
        password_data: schemas.PasswordChange,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Смена пароля пользователя
    """
    # Проверка текущего пароля
    if not dependencies.verify_password(
            password_data.current_password,
            current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текущий пароль неверен"
        )

    # Обновление пароля
    current_user.hashed_password = dependencies.get_password_hash(
        password_data.new_password
    )
    current_user.updated_at = datetime.utcnow()
    session.add(current_user)
    session.commit()

    logger.info(f"Пароль изменен для пользователя: {current_user.email}")

    return schemas.SuccessResponse(
        message="Пароль успешно изменен"
    )


@router.get("/me/stats", response_model=schemas.UserStatsResponse)
async def get_user_stats(
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Получение статистики пользователя
    """
    # Общее время просмотра
    total_watch_time = session.exec(
        select(func.sum(models.WatchHistory.watch_duration_seconds))
        .where(models.WatchHistory.user_id == current_user.id)
    ).first() or 0

    # Фильмы просмотрены
    movies_watched = session.exec(
        select(func.count(models.WatchHistory.id))
        .join(models.Content)
        .join(models.ContentType)
        .where(
            and_(
                models.WatchHistory.user_id == current_user.id,
                models.ContentType.code == "movie"
            )
        )
    ).first() or 0

    # Сериалы просмотрены
    series_watched = session.exec(
        select(func.count(func.distinct(models.WatchHistory.content_id)))
        .join(models.Content)
        .join(models.ContentType)
        .where(
            and_(
                models.WatchHistory.user_id == current_user.id,
                models.ContentType.code == "series"
            )
        )
    ).first() or 0

    # Эпизоды просмотрены
    episodes_watched = session.exec(
        select(func.count(models.WatchHistory.id))
        .join(models.Content)
        .join(models.ContentType)
        .where(
            and_(
                models.WatchHistory.user_id == current_user.id,
                models.ContentType.code == "series",
                models.WatchHistory.episode_id.is_not(None)
            )
        )
    ).first() or 0

    # Количество оценок
    ratings_count = session.exec(
        select(func.count(models.Rating.id))
        .where(models.Rating.user_id == current_user.id)
    ).first() or 0

    # Количество закладок
    watchlist_count = session.exec(
        select(func.count(models.Watchlist.id))
        .where(models.Watchlist.user_id == current_user.id)
    ).first() or 0

    # Любимый жанр
    favorite_genre = session.exec(
        select(models.Genre.name)
        .join(models.ContentGenre)
        .join(models.Content)
        .join(models.WatchHistory)
        .where(models.WatchHistory.user_id == current_user.id)
        .group_by(models.Genre.id)
        .order_by(func.count(models.WatchHistory.id).desc())
        .limit(1)
    ).first()

    # Последний просмотр
    last_watched = session.exec(
        select(models.WatchHistory.watched_at)
        .where(models.WatchHistory.user_id == current_user.id)
        .order_by(models.WatchHistory.watched_at.desc())
        .limit(1)
    ).first()

    # Средняя оценка
    average_rating = session.exec(
        select(func.avg(models.Rating.rating_value))
        .where(models.Rating.user_id == current_user.id)
    ).first()

    return schemas.UserStatsResponse(
        total_watch_time_minutes=total_watch_time // 60,
        movies_watched=movies_watched,
        series_watched=series_watched,
        episodes_watched=episodes_watched,
        ratings_count=ratings_count,
        watchlist_count=watchlist_count,
        favorite_genre=favorite_genre,
        last_watched=last_watched,
        average_rating=float(average_rating) if average_rating else None
    )


@router.get("/me/watch-history", response_model=List[schemas.WatchHistoryResponse])
async def get_watch_history(
        pagination: schemas.PaginationParams = Depends(),
        content_type_id: Optional[int] = None,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Получение истории просмотров пользователя
    """
    query = select(models.WatchHistory).where(
        models.WatchHistory.user_id == current_user.id
    )

    if content_type_id:
        query = query.join(models.Content).where(
            models.Content.content_type_id == content_type_id
        )

    query = query.order_by(models.WatchHistory.watched_at.desc())

    # Пагинация
    offset = (pagination.page - 1) * pagination.size
    query = query.offset(offset).limit(pagination.size)

    history = session.exec(query).all()
    return history


@router.get("/me/continue-watching", response_model=List[schemas.ContinueWatchingResponse])
async def get_continue_watching(
        limit: int = Query(default=10, le=50),
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Получение списка "Продолжить просмотр"
    """
    # Находим недосмотренные фильмы/сериалы
    query = select(models.WatchHistory).where(
        and_(
            models.WatchHistory.user_id == current_user.id,
            models.WatchHistory.progress_percentage < 90,  # Не завершены
            models.WatchHistory.watched_at >= datetime.utcnow() - timedelta(days=30)
        )
    ).order_by(models.WatchHistory.watched_at.desc()).limit(limit)

    history = session.exec(query).all()

    result = []
    seen_content_ids = set()

    for item in history:
        if item.content_id in seen_content_ids:
            continue

        seen_content_ids.add(item.content_id)
        result.append(schemas.ContinueWatchingResponse(
            content=item.content,
            episode=item.episode,
            progress_percentage=item.progress_percentage,
            watch_duration_seconds=item.watch_duration_seconds,
            last_watched_at=item.watched_at
        ))

    return result


@router.get("/me/devices", response_model=List[schemas.UserDeviceResponse])
async def get_user_devices(
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Получение устройств пользователя
    """
    devices = session.exec(
        select(models.UserDevice).where(
            models.UserDevice.user_id == current_user.id,
            models.UserDevice.is_active == True
        ).order_by(models.UserDevice.last_active.desc())
    ).all()

    return devices


@router.post("/me/devices", response_model=schemas.UserDeviceResponse)
async def add_user_device(
        device_data: schemas.UserDeviceCreate,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Добавление устройства пользователя
    """
    # Проверяем существующее устройство
    existing = session.exec(
        select(models.UserDevice).where(
            and_(
                models.UserDevice.user_id == current_user.id,
                models.UserDevice.device_id == device_data.device_id
            )
        )
    ).first()

    if existing:
        # Обновляем существующее устройство
        existing.device_name = device_data.device_name
        existing.fcm_token = device_data.fcm_token
        existing.last_active = datetime.utcnow()
        device = existing
    else:
        # Создаем новое устройство
        device = models.UserDevice(
            user_id=current_user.id,
            device_id=device_data.device_id,
            device_type=device_data.device_type,
            device_name=device_data.device_name,
            fcm_token=device_data.fcm_token
        )
        session.add(device)

    session.commit()
    session.refresh(device)
    return device


@router.delete("/me/devices/{device_id}")
async def remove_user_device(
        device_id: str,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Удаление устройства пользователя
    """
    device = session.exec(
        select(models.UserDevice).where(
            and_(
                models.UserDevice.user_id == current_user.id,
                models.UserDevice.device_id == device_id
            )
        )
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено"
        )

    device.is_active = False
    session.add(device)
    session.commit()

    return schemas.SuccessResponse(
        message="Устройство удалено"
    )


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user_by_id(
        user_id: int,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    """
    Получение пользователя по ID (только для staff/superuser)
    """
    if not current_user.is_staff and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )

    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    return user


@router.get("/", response_model=schemas.PaginatedResponse)
async def get_users(
        pagination: schemas.PaginationParams = Depends(),
        is_active: Optional[bool] = None,
        is_staff: Optional[bool] = None,
        subscription_tier_id: Optional[int] = None,
        search: Optional[str] = None,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_superuser)
):
    """
    Получение списка пользователей (только для суперпользователя)
    """
    query = select(models.User)

    # Фильтры
    if is_active is not None:
        query = query.where(models.User.is_active == is_active)

    if is_staff is not None:
        query = query.where(models.User.is_staff == is_staff)

    if subscription_tier_id is not None:
        query = query.where(models.User.subscription_tier_id == subscription_tier_id)

    if search:
        query = query.where(
            or_(
                models.User.email.ilike(f"%{search}%"),
                models.User.username.ilike(f"%{search}%"),
                models.User.full_name.ilike(f"%{search}%")
            )
        )

    # Общее количество
    total = session.exec(
        select(func.count()).select_from(query.subquery())
    ).first()

    # Пагинация
    offset = (pagination.page - 1) * pagination.size
    query = query.order_by(models.User.created_at.desc())
    query = query.offset(offset).limit(pagination.size)

    users = session.exec(query).all()

    return schemas.PaginatedResponse(
        items=users,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=(total + pagination.size - 1) // pagination.size,
        has_next=offset + len(users) < total,
        has_prev=pagination.page > 1
    )


@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
        user_id: int,
        user_update: schemas.UserUpdate,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_superuser)
):
    """
    Обновление пользователя (только для суперпользователя)
    """
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    update_data = user_update.dict(exclude_unset=True)

    # Проверка уникальности email
    if "email" in update_data and update_data["email"] != user.email:
        existing = dependencies.get_user_by_email(update_data["email"], session)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже используется"
            )

    # Проверка уникальности username
    if "username" in update_data and update_data["username"] != user.username:
        existing = dependencies.get_user_by_username(update_data["username"], session)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Имя пользователя уже используется"
            )

    # Обновляем поля
    for key, value in update_data.items():
        setattr(user, key, value)

    user.updated_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info(f"Пользователь обновлен администратором: {user.email}")
    return user


@router.delete("/{user_id}")
async def delete_user(
        user_id: int,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_superuser)
):
    """
    Удаление пользователя (только для суперпользователя)
    """
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # Мягкое удаление
    user.is_active = False
    user.email = f"{user.email}.deleted.{datetime.utcnow().timestamp()}"
    user.username = f"{user.username}.deleted.{datetime.utcnow().timestamp()}"
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()

    logger.info(f"Пользователь деактивирован: {user_id}")

    return schemas.SuccessResponse(
        message="Пользователь удален"
    )