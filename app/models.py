"""
Модели данных SQLModel для онлайн-кинотеатра
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, date
from pydantic import EmailStr, validator, HttpUrl
from enum import Enum as PyEnum
import uuid

if TYPE_CHECKING:
    from sqlmodel import Session


# ============ ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ ============

class Status(str, PyEnum):
    """Статусы для различных сущностей"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    DELETED = "deleted"


class MediaType(str, PyEnum):
    """Типы медиа-файлов"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    SUBTITLE = "subtitle"


# ============ СПРАВОЧНИКИ ============

class ContentType(SQLModel, table=True):
    """Тип контента"""
    __tablename__ = "content_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    icon_url: Optional[str] = Field(default=None, max_length=500)
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Связи
    contents: List["Content"] = Relationship(back_populates="content_type_rel")

    class Config:
        schema_extra = {
            "example": {
                "code": "movie",
                "name": "Фильм",
                "description": "Полнометражные фильмы",
                "sort_order": 1
            }
        }


class AgeRating(SQLModel, table=True):
    """Возрастной рейтинг"""
    __tablename__ = "age_ratings"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=20)
    name: str = Field(max_length=100)
    min_age: Optional[int] = Field(default=None)
    description: Optional[str] = Field(default=None)
    icon_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Связи
    contents: List["Content"] = Relationship(back_populates="age_rating_rel")

    class Config:
        schema_extra = {
            "example": {
                "code": "PG-13",
                "name": "С 13 лет",
                "min_age": 13,
                "description": "Может содержать сцены насилия"
            }
        }


class SubscriptionTier(SQLModel, table=True):
    """Уровень подписки"""
    __tablename__ = "subscription_tiers"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None)
    price_monthly: Optional[float] = Field(default=None, ge=0)
    price_yearly: Optional[float] = Field(default=None, ge=0)
    max_simultaneous_streams: int = Field(default=1, ge=1)
    max_video_quality: str = Field(default="HD", max_length=20)
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Связи
    features: List["SubscriptionFeature"] = Relationship(back_populates="tier")
    users: List["User"] = Relationship(back_populates="subscription_tier_rel")

    class Config:
        schema_extra = {
            "example": {
                "code": "premium",
                "name": "Премиум",
                "price_monthly": 599,
                "max_simultaneous_streams": 4
            }
        }


class SubscriptionFeature(SQLModel, table=True):
    """Особенности подписки"""
    __tablename__ = "subscription_features"

    id: Optional[int] = Field(default=None, primary_key=True)
    tier_id: int = Field(foreign_key="subscription_tiers.id")
    feature: str = Field(max_length=200)
    description: Optional[str] = Field(default=None)
    is_included: bool = Field(default=True)
    sort_order: int = Field(default=0)

    tier: "SubscriptionTier" = Relationship(back_populates="features")

    class Config:
        schema_extra = {
            "example": {
                "feature": "Без рекламы",
                "is_included": True
            }
        }


class VideoQuality(SQLModel, table=True):
    """Качество видео"""
    __tablename__ = "video_qualities"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=20)
    name: str = Field(max_length=100)
    width: int = Field(ge=240)
    height: int = Field(ge=240)
    bitrate: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = Field(default=None)
    sort_order: int = Field(default=0)

    # Связи
    episodes: List["Episode"] = Relationship(back_populates="video_quality_rel")

    class Config:
        schema_extra = {
            "example": {
                "code": "4k",
                "name": "4K Ultra HD",
                "width": 3840,
                "height": 2160
            }
        }


class Genre(SQLModel, table=True):
    """Жанр контента"""
    __tablename__ = "genres"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    description: Optional[str] = Field(default=None)
    icon_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Связи
    contents: List["Content"] = Relationship(
        back_populates="genres",
        link_model="ContentGenre"
    )

    class Config:
        schema_extra = {
            "example": {
                "name": "Научная фантастика",
                "description": "Фильмы о будущем и технологиях"
            }
        }


class Country(SQLModel, table=True):
    """Страна производства"""
    __tablename__ = "countries"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=2)  # ISO код
    name: str = Field(max_length=100)
    name_en: Optional[str] = Field(default=None, max_length=100)
    flag_url: Optional[str] = Field(default=None, max_length=500)

    # Связи
    contents: List["Content"] = Relationship(
        back_populates="countries",
        link_model="ContentCountry"
    )

    class Config:
        schema_extra = {
            "example": {
                "code": "US",
                "name": "США",
                "name_en": "United States"
            }
        }


# ============ ОСНОВНЫЕ МОДЕЛИ ============

class User(SQLModel, table=True):
    """Пользователь"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        unique=True,
        index=True
    )
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    username: str = Field(index=True, max_length=100)
    hashed_password: str = Field(max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=200)

    # Внешние ключи
    subscription_tier_id: int = Field(
        foreign_key="subscription_tiers.id",
        default=1
    )

    # Статус и метаданные
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    is_staff: bool = Field(default=False)
    is_superuser: bool = Field(default=False)

    # Даты
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    last_login: Optional[datetime] = Field(default=None)
    email_verified_at: Optional[datetime] = Field(default=None)

    # Профиль
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    bio: Optional[str] = Field(default=None, max_length=1000)
    language: str = Field(default="ru", max_length=10)
    timezone: str = Field(default="Europe/Moscow", max_length=50)

    # Статистика
    watch_time_minutes: int = Field(default=0, ge=0)

    # Связи
    subscription_tier_rel: "SubscriptionTier" = Relationship(back_populates="users")
    watch_history: List["WatchHistory"] = Relationship(back_populates="user")
    ratings: List["Rating"] = Relationship(back_populates="user")
    watchlist_items: List["Watchlist"] = Relationship(back_populates="user")
    devices: List["UserDevice"] = Relationship(back_populates="user")
    payments: List["Payment"] = Relationship(back_populates="user")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "cinemalover",
                "full_name": "Иван Иванов"
            }
        }


class Content(SQLModel, table=True):
    """Контент (фильмы, сериалы)"""
    __tablename__ = "contents"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        unique=True,
        index=True
    )
    title: str = Field(index=True, max_length=255)
    original_title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    short_description: Optional[str] = Field(default=None, max_length=500)

    # Внешние ключи
    content_type_id: int = Field(foreign_key="content_types.id", default=1)
    age_rating_id: int = Field(foreign_key="age_ratings.id", default=3)

    # Основная информация
    release_year: int = Field(ge=1888)  # Первый фильм 1888
    duration_minutes: int = Field(default=0, ge=0)
    imdb_id: Optional[str] = Field(default=None, max_length=20)
    tmdb_id: Optional[str] = Field(default=None, max_length=20)
    kinopoisk_id: Optional[str] = Field(default=None, max_length=20)

    # Медиа
    poster_url: Optional[str] = Field(default=None, max_length=500)
    backdrop_url: Optional[str] = Field(default=None, max_length=500)
    trailer_url: Optional[str] = Field(default=None, max_length=500)

    # Рейтинги
    imdb_rating: Optional[float] = Field(default=None, ge=0, le=10)
    kinopoisk_rating: Optional[float] = Field(default=None, ge=0, le=10)
    our_rating: Optional[float] = Field(default=None, ge=0, le=10)

    # Метаданные
    director: Optional[str] = Field(default=None, max_length=200)
    writer: Optional[str] = Field(default=None, max_length=500)
    cast: Optional[str] = Field(default=None)  # JSON строка

    # Статус
    is_featured: bool = Field(default=False)
    is_popular: bool = Field(default=False)
    is_new: bool = Field(default=True)
    is_available: bool = Field(default=True)
    requires_subscription: bool = Field(default=False)

    # Даты
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    available_from: datetime = Field(default_factory=datetime.utcnow)
    available_to: Optional[datetime] = Field(default=None)

    # Технические
    views_count: int = Field(default=0, ge=0)
    watch_count: int = Field(default=0, ge=0)

    # Связи
    content_type_rel: "ContentType" = Relationship(back_populates="contents")
    age_rating_rel: "AgeRating" = Relationship(back_populates="contents")
    genres: List["Genre"] = Relationship(
        back_populates="contents",
        link_model="ContentGenre"
    )
    countries: List["Country"] = Relationship(
        back_populates="contents",
        link_model="ContentCountry"
    )
    actors: List["Actor"] = Relationship(
        back_populates="contents",
        link_model="ContentActor"
    )
    seasons: List["Season"] = Relationship(back_populates="content")
    episodes: List["Episode"] = Relationship(back_populates="content")
    ratings: List["Rating"] = Relationship(back_populates="content")
    watch_history: List["WatchHistory"] = Relationship(back_populates="content")
    watchlist_items: List["Watchlist"] = Relationship(back_populates="content")
    media_files: List["MediaFile"] = Relationship(back_populates="content")

    class Config:
        schema_extra = {
            "example": {
                "title": "Интерстеллар",
                "original_title": "Interstellar",
                "release_year": 2014,
                "duration_minutes": 169,
                "director": "Кристофер Нолан"
            }
        }


class Actor(SQLModel, table=True):
    """Актер"""
    __tablename__ = "actors"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str = Field(index=True, max_length=200)
    birth_date: Optional[date] = Field(default=None)
    death_date: Optional[date] = Field(default=None)
    biography: Optional[str] = Field(default=None)
    photo_url: Optional[str] = Field(default=None, max_length=500)
    imdb_id: Optional[str] = Field(default=None, max_length=20)
    tmdb_id: Optional[str] = Field(default=None, max_length=20)

    # Статистика
    popularity: float = Field(default=0.0, ge=0)

    # Связи
    contents: List["Content"] = Relationship(
        back_populates="actors",
        link_model="ContentActor"
    )

    class Config:
        schema_extra = {
            "example": {
                "full_name": "Мэттью Макконахи",
                "birth_date": "1969-11-04"
            }
        }


class Season(SQLModel, table=True):
    """Сезон сериала"""
    __tablename__ = "seasons"

    id: Optional[int] = Field(default=None, primary_key=True)
    content_id: int = Field(foreign_key="contents.id")
    season_number: int = Field(ge=1)
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    release_year: Optional[int] = Field(default=None)
    poster_url: Optional[str] = Field(default=None, max_length=500)
    episode_count: int = Field(default=0, ge=0)

    # Связи
    content: "Content" = Relationship(back_populates="seasons")
    episodes: List["Episode"] = Relationship(back_populates="season")

    class Config:
        schema_extra = {
            "example": {
                "season_number": 1,
                "title": "Первый сезон",
                "episode_count": 10
            }
        }


class Episode(SQLModel, table=True):
    """Эпизод сериала"""
    __tablename__ = "episodes"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        unique=True,
        index=True
    )
    season_id: int = Field(foreign_key="seasons.id")
    content_id: int = Field(foreign_key="contents.id")
    episode_number: int = Field(ge=1)
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    duration_minutes: int = Field(default=0, ge=0)

    # Внешние ключи
    video_quality_id: Optional[int] = Field(
        default=None,
        foreign_key="video_qualities.id"
    )

    # Медиа
    video_url: str = Field(max_length=500)
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    preview_url: Optional[str] = Field(default=None, max_length=500)

    # Метаданные
    director: Optional[str] = Field(default=None, max_length=200)
    writer: Optional[str] = Field(default=None, max_length=200)
    release_date: Optional[date] = Field(default=None)

    # Статистика
    views_count: int = Field(default=0, ge=0)

    # Связи
    season: "Season" = Relationship(back_populates="episodes")
    content: "Content" = Relationship(back_populates="episodes")
    video_quality_rel: Optional["VideoQuality"] = Relationship(
        back_populates="episodes"
    )
    watch_history: List["WatchHistory"] = Relationship(back_populates="episode")
    media_files: List["MediaFile"] = Relationship(back_populates="episode")

    class Config:
        schema_extra = {
            "example": {
                "episode_number": 5,
                "title": "Поворотный момент",
                "duration_minutes": 47
            }
        }


class MediaFile(SQLModel, table=True):
    """Медиа файл"""
    __tablename__ = "media_files"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        unique=True,
        index=True
    )
    content_id: Optional[int] = Field(default=None, foreign_key="contents.id")
    episode_id: Optional[int] = Field(default=None, foreign_key="episodes.id")
    file_type: MediaType = Field(default=MediaType.VIDEO)
    file_url: str = Field(max_length=500)
    file_size_bytes: Optional[int] = Field(default=None, ge=0)
    duration_seconds: Optional[int] = Field(default=None, ge=0)
    quality: Optional[str] = Field(default=None, max_length=20)
    language: str = Field(default="ru", max_length=10)
    is_main: bool = Field(default=False)
    is_available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Связи
    content: Optional["Content"] = Relationship(back_populates="media_files")
    episode: Optional["Episode"] = Relationship(back_populates="media_files")

    class Config:
        schema_extra = {
            "example": {
                "file_type": "video",
                "file_url": "https://cdn.example.com/video.mp4",
                "quality": "1080p",
                "language": "ru"
            }
        }


# ============ ТАБЛИЦЫ СВЯЗЕЙ ============

class ContentGenre(SQLModel, table=True):
    """Связь контента и жанров"""
    __tablename__ = "content_genres"

    content_id: int = Field(foreign_key="contents.id", primary_key=True)
    genre_id: int = Field(foreign_key="genres.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContentActor(SQLModel, table=True):
    """Связь контента и актеров"""
    __tablename__ = "content_actors"

    content_id: int = Field(foreign_key="contents.id", primary_key=True)
    actor_id: int = Field(foreign_key="actors.id", primary_key=True)
    role: Optional[str] = Field(default=None, max_length=100)  # Роль актера
    is_main: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContentCountry(SQLModel, table=True):
    """Связь контента и стран"""
    __tablename__ = "content_countries"

    content_id: int = Field(foreign_key="contents.id", primary_key=True)
    country_id: int = Field(foreign_key="countries.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============ ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ ============

class WatchHistory(SQLModel, table=True):
    """История просмотров"""
    __tablename__ = "watch_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    content_id: int = Field(foreign_key="contents.id")
    episode_id: Optional[int] = Field(default=None, foreign_key="episodes.id")

    # Прогресс
    watched_at: datetime = Field(default_factory=datetime.utcnow)
    watch_duration_seconds: int = Field(default=0, ge=0)
    progress_percentage: float = Field(default=0.0, ge=0, le=100)
    is_completed: bool = Field(default=False)

    # Технические
    device_type: Optional[str] = Field(default=None, max_length=50)
    ip_address: Optional[str] = Field(default=None, max_length=45)

    # Связи
    user: "User" = Relationship(back_populates="watch_history")
    content: "Content" = Relationship(back_populates="watch_history")
    episode: Optional["Episode"] = Relationship(back_populates="watch_history")

    class Config:
        schema_extra = {
            "example": {
                "watch_duration_seconds": 1200,
                "progress_percentage": 65.5,
                "device_type": "web"
            }
        }


class Rating(SQLModel, table=True):
    """Рейтинг пользователя"""
    __tablename__ = "ratings"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    content_id: int = Field(foreign_key="contents.id")
    rating_value: float = Field(ge=0.5, le=5.0, multiple_of=0.5)
    review: Optional[str] = Field(default=None)
    is_public: bool = Field(default=True)
    likes_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Связи
    user: "User" = Relationship(back_populates="ratings")
    content: "Content" = Relationship(back_populates="ratings")
    helpful_votes: List["HelpfulVote"] = Relationship(back_populates="rating")

    class Config:
        schema_extra = {
            "example": {
                "rating_value": 4.5,
                "review": "Отличный фильм с глубоким смыслом!"
            }
        }


class HelpfulVote(SQLModel, table=True):
    """Оценка полезности отзыва"""
    __tablename__ = "helpful_votes"

    id: Optional[int] = Field(default=None, primary_key=True)
    rating_id: int = Field(foreign_key="ratings.id")
    user_id: int = Field(foreign_key="users.id")
    is_helpful: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    rating: "Rating" = Relationship(back_populates="helpful_votes")


class Watchlist(SQLModel, table=True):
    """Закладки пользователя"""
    __tablename__ = "watchlist"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    content_id: int = Field(foreign_key="contents.id")
    added_at: datetime = Field(default_factory=datetime.utcnow)
    priority: int = Field(default=0, ge=0, le=10)
    notes: Optional[str] = Field(default=None, max_length=500)

    # Связи
    user: "User" = Relationship(back_populates="watchlist_items")
    content: "Content" = Relationship(back_populates="watchlist_items")

    class Config:
        schema_extra = {
            "example": {
                "priority": 3,
                "notes": "Посмотреть на выходных"
            }
        }


# ============ СИСТЕМНЫЕ МОДЕЛИ ============

class UserDevice(SQLModel, table=True):
    """Устройства пользователя"""
    __tablename__ = "user_devices"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    device_id: str = Field(max_length=255, index=True)
    device_type: str = Field(max_length=50)  # web, android, ios
    device_name: Optional[str] = Field(default=None, max_length=100)
    fcm_token: Optional[str] = Field(default=None, max_length=500)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="devices")


class Notification(SQLModel, table=True):
    """Уведомления"""
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: str = Field(max_length=200)
    message: str = Field(max_length=1000)
    notification_type: str = Field(max_length=50)  # info, warning, success
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = Field(default=None)


class Payment(SQLModel, table=True):
    """Платежи"""
    __tablename__ = "payments"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        unique=True,
        index=True
    )
    user_id: int = Field(foreign_key="users.id")
    subscription_tier_id: int = Field(foreign_key="subscription_tiers.id")
    amount: float = Field(ge=0)
    currency: str = Field(default="RUB", max_length=3)
    status: str = Field(default="pending", max_length=20)
    payment_method: str = Field(max_length=50)
    payment_gateway: str = Field(max_length=50)
    gateway_transaction_id: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None)
    metadata: Optional[str] = Field(default=None)  # JSON
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    paid_at: Optional[datetime] = Field(default=None)

    # Связи
    user: "User" = Relationship(back_populates="payments")


class SubscriptionHistory(SQLModel, table=True):
    """История подписок"""
    __tablename__ = "subscription_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    subscription_tier_id: int = Field(foreign_key="subscription_tiers.id")
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = Field(default=None)
    status: str = Field(default="active", max_length=20)
    auto_renew: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    """Лог аудита"""
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    action: str = Field(max_length=100)
    table_name: str = Field(max_length=100)
    record_id: Optional[int] = Field(default=None)
    old_values: Optional[str] = Field(default=None)  # JSON
    new_values: Optional[str] = Field(default=None)  # JSON
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============ ИНДЕКСЫ И ОГРАНИЧЕНИЯ ============

# Создаем составные индексы для улучшения производительности
from sqlmodel import Index

# Уникальные ограничения
User.__table_args__ = (
    Index('ix_users_email_lower', 'email', postgresql_using='btree'),
    Index('ix_users_username_lower', 'username', postgresql_using='btree'),
)

Content.__table_args__ = (
    Index('ix_contents_title_tsvector', 'title', postgresql_using='gin'),
    Index('ix_contents_release_year', 'release_year'),
    Index('ix_contents_imdb_rating', 'imdb_rating'),
)

Rating.__table_args__ = (
    Index('ix_ratings_user_content', 'user_id', 'content_id', unique=True),
)

Watchlist.__table_args__ = (
    Index('ix_watchlist_user_content', 'user_id', 'content_id', unique=True),
)

WatchHistory.__table_args__ = (
    Index('ix_watch_history_user_content', 'user_id', 'content_id'),
    Index('ix_watch_history_watched_at', 'watched_at'),
)