"""
Pydantic схемы для валидации и сериализации
"""

from sqlmodel import SQLModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, timedelta
from pydantic import EmailStr, validator, Field as PydanticField, HttpUrl
from enum import Enum
import re
from models import MediaType, Status


# ============ БАЗОВЫЕ СХЕМЫ ============

class BaseSchema(SQLModel):
    """Базовая схема с общими методами"""

    class Config:
        from_attributes = True
        use_enum_values = True
        arbitrary_types_allowed = True


class PaginationParams(BaseSchema):
    """Параметры пагинации"""
    page: int = PydanticField(default=1, ge=1, description="Номер страницы")
    size: int = PydanticField(default=20, ge=1, le=100, description="Размер страницы")
    sort_by: Optional[str] = PydanticField(default="created_at", description="Поле для сортировки")
    sort_order: str = PydanticField(default="desc", description="Порядок сортировки")

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order должен быть "asc" или "desc"')
        return v


class PaginatedResponse(BaseSchema):
    """Ответ с пагинацией"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


# ============ СПРАВОЧНИКИ ============

class ContentTypeBase(BaseSchema):
    """Базовая схема типа контента"""
    code: str = PydanticField(..., min_length=2, max_length=50, description="Уникальный код")
    name: str = PydanticField(..., max_length=100, description="Название")
    description: Optional[str] = PydanticField(None, description="Описание")
    icon_url: Optional[HttpUrl] = PydanticField(None, description="URL иконки")
    sort_order: int = PydanticField(default=0, ge=0, description="Порядок сортировки")


class ContentTypeCreate(ContentTypeBase):
    """Создание типа контента"""
    pass


class ContentTypeUpdate(BaseSchema):
    """Обновление типа контента"""
    name: Optional[str] = PydanticField(None, max_length=100)
    description: Optional[str] = None
    icon_url: Optional[HttpUrl] = None
    sort_order: Optional[int] = PydanticField(None, ge=0)
    is_active: Optional[bool] = None


class ContentTypeResponse(ContentTypeBase):
    """Ответ с типом контента"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class AgeRatingBase(BaseSchema):
    """Базовая схема возрастного рейтинга"""
    code: str = PydanticField(..., max_length=20)
    name: str = PydanticField(..., max_length=100)
    min_age: Optional[int] = PydanticField(None, ge=0, le=100)
    description: Optional[str] = None
    icon_url: Optional[HttpUrl] = None


class AgeRatingResponse(AgeRatingBase):
    """Ответ с возрастным рейтингом"""
    id: int
    is_active: bool
    created_at: datetime


class SubscriptionTierBase(BaseSchema):
    """Базовая схема тарифа подписки"""
    code: str = PydanticField(..., max_length=50)
    name: str = PydanticField(..., max_length=100)
    description: Optional[str] = None
    price_monthly: Optional[float] = PydanticField(None, ge=0)
    price_yearly: Optional[float] = PydanticField(None, ge=0)
    max_simultaneous_streams: int = PydanticField(default=1, ge=1)
    max_video_quality: str = PydanticField(default="HD", max_length=20)
    sort_order: int = PydanticField(default=0, ge=0)


class SubscriptionTierCreate(SubscriptionTierBase):
    """Создание тарифа подписки"""
    features: List[str] = PydanticField(default=[], description="Список фич")


class SubscriptionTierResponse(SubscriptionTierBase):
    """Ответ с тарифом подписки"""
    id: int
    is_active: bool
    features: List["SubscriptionFeatureResponse"] = []
    created_at: datetime
    updated_at: Optional[datetime]


class SubscriptionFeatureResponse(BaseSchema):
    """Ответ с фичей подписки"""
    id: int
    feature: str
    description: Optional[str]
    is_included: bool
    sort_order: int


class VideoQualityBase(BaseSchema):
    """Базовая схема качества видео"""
    code: str = PydanticField(..., max_length=20)
    name: str = PydanticField(..., max_length=100)
    width: int = PydanticField(..., ge=240)
    height: int = PydanticField(..., ge=240)
    bitrate: Optional[int] = PydanticField(None, ge=0)
    description: Optional[str] = None
    sort_order: int = PydanticField(default=0, ge=0)


class VideoQualityResponse(VideoQualityBase):
    """Ответ с качеством видео"""
    id: int


class GenreBase(BaseSchema):
    """Базовая схема жанра"""
    name: str = PydanticField(..., max_length=100)
    description: Optional[str] = None
    icon_url: Optional[HttpUrl] = None


class GenreResponse(GenreBase):
    """Ответ с жанром"""
    id: int
    is_active: bool
    created_at: datetime


class CountryBase(BaseSchema):
    """Базовая схема страны"""
    code: str = PydanticField(..., max_length=2, description="ISO код страны")
    name: str = PydanticField(..., max_length=100)
    name_en: Optional[str] = PydanticField(None, max_length=100)
    flag_url: Optional[HttpUrl] = None


class CountryResponse(CountryBase):
    """Ответ со страной"""
    id: int


# ============ ПОЛЬЗОВАТЕЛИ ============

class UserBase(BaseSchema):
    """Базовая схема пользователя"""
    email: EmailStr = PydanticField(..., description="Email пользователя")
    username: str = PydanticField(..., min_length=3, max_length=50, description="Имя пользователя")
    full_name: Optional[str] = PydanticField(None, max_length=200, description="Полное имя")

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Имя пользователя может содержать только буквы, цифры и подчеркивания')
        return v


class UserCreate(UserBase):
    """Создание пользователя"""
    password: str = PydanticField(..., min_length=8, max_length=128, description="Пароль")
    confirm_password: str = PydanticField(..., description="Подтверждение пароля")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Пароли не совпадают')
        return v

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен быть минимум 8 символов')
        if not any(c.isupper() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        return v


class UserUpdate(BaseSchema):
    """Обновление пользователя"""
    email: Optional[EmailStr] = None
    username: Optional[str] = PydanticField(None, min_length=3, max_length=50)
    full_name: Optional[str] = PydanticField(None, max_length=200)
    avatar_url: Optional[HttpUrl] = None
    bio: Optional[str] = PydanticField(None, max_length=1000)
    language: Optional[str] = PydanticField(None, max_length=10)
    timezone: Optional[str] = PydanticField(None, max_length=50)

    @validator('username')
    def validate_username_update(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Имя пользователя может содержать только буквы, цифры и подчеркивания')
        return v


class UserProfileUpdate(BaseSchema):
    """Обновление профиля пользователя"""
    full_name: Optional[str] = PydanticField(None, max_length=200)
    avatar_url: Optional[HttpUrl] = None
    bio: Optional[str] = PydanticField(None, max_length=1000)
    language: Optional[str] = PydanticField(None, max_length=10)
    timezone: Optional[str] = PydanticField(None, max_length=50)


class PasswordChange(BaseSchema):
    """Смена пароля"""
    current_password: str = PydanticField(..., description="Текущий пароль")
    new_password: str = PydanticField(..., min_length=8, max_length=128, description="Новый пароль")
    confirm_password: str = PydanticField(..., description="Подтверждение нового пароля")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Новые пароли не совпадают')
        return v

    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен быть минимум 8 символов')
        if not any(c.isupper() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        return v


class UserResponse(UserBase):
    """Ответ с пользователем"""
    id: int
    uuid: str
    is_active: bool
    is_verified: bool
    is_staff: bool
    subscription_tier: SubscriptionTierResponse
    avatar_url: Optional[HttpUrl]
    bio: Optional[str]
    language: str
    timezone: str
    watch_time_minutes: int
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]


class UserStatsResponse(BaseSchema):
    """Статистика пользователя"""
    total_watch_time_minutes: int
    movies_watched: int
    series_watched: int
    episodes_watched: int
    ratings_count: int
    watchlist_count: int
    favorite_genre: Optional[str]
    last_watched: Optional[datetime]
    average_rating: Optional[float]


class UserDeviceCreate(BaseSchema):
    """Добавление устройства"""
    device_id: str = PydanticField(..., max_length=255)
    device_type: str = PydanticField(..., max_length=50)
    device_name: Optional[str] = PydanticField(None, max_length=100)
    fcm_token: Optional[str] = PydanticField(None, max_length=500)


class UserDeviceResponse(BaseSchema):
    """Ответ с устройством"""
    id: int
    device_id: str
    device_type: str
    device_name: Optional[str]
    last_active: datetime
    is_active: bool
    created_at: datetime


# ============ КОНТЕНТ ============

class ContentBase(BaseSchema):
    """Базовая схема контента"""
    title: str = PydanticField(..., max_length=255, description="Название")
    original_title: Optional[str] = PydanticField(None, max_length=255, description="Оригинальное название")
    description: Optional[str] = None
    short_description: Optional[str] = PydanticField(None, max_length=500, description="Краткое описание")
    content_type_id: int = PydanticField(..., description="ID типа контента")
    age_rating_id: int = PydanticField(..., description="ID возрастного рейтинга")
    release_year: int = PydanticField(..., ge=1888, le=2100, description="Год выпуска")
    duration_minutes: int = PydanticField(default=0, ge=0, description="Длительность в минутах")
    director: Optional[str] = PydanticField(None, max_length=200, description="Режиссер")
    writer: Optional[str] = PydanticField(None, max_length=500, description="Сценарист")
    imdb_id: Optional[str] = PydanticField(None, max_length=20, description="ID IMDB")
    tmdb_id: Optional[str] = PydanticField(None, max_length=20, description="ID TMDB")
    kinopoisk_id: Optional[str] = PydanticField(None, max_length=20, description="ID Кинопоиска")

    @validator('release_year')
    def validate_release_year(cls, v):
        current_year = datetime.now().year
        if v > current_year + 5:
            raise ValueError(f'Год выпуска не может быть больше {current_year + 5}')
        return v


class ContentCreate(ContentBase):
    """Создание контента"""
    poster_url: Optional[HttpUrl] = None
    backdrop_url: Optional[HttpUrl] = None
    trailer_url: Optional[HttpUrl] = None
    imdb_rating: Optional[float] = PydanticField(None, ge=0, le=10)
    kinopoisk_rating: Optional[float] = PydanticField(None, ge=0, le=10)
    is_featured: bool = False
    is_popular: bool = False
    is_new: bool = True
    requires_subscription: bool = False
    genre_ids: List[int] = PydanticField(default=[], description="ID жанров")
    country_ids: List[int] = PydanticField(default=[], description="ID стран")
    actor_ids: List[int] = PydanticField(default=[], description="ID актеров")

    @validator('imdb_rating', 'kinopoisk_rating')
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 10):
            raise ValueError('Рейтинг должен быть от 0 до 10')
        return v


class ContentUpdate(BaseSchema):
    """Обновление контента"""
    title: Optional[str] = PydanticField(None, max_length=255)
    original_title: Optional[str] = PydanticField(None, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = PydanticField(None, max_length=500)
    release_year: Optional[int] = PydanticField(None, ge=1888, le=2100)
    duration_minutes: Optional[int] = PydanticField(None, ge=0)
    director: Optional[str] = PydanticField(None, max_length=200)
    writer: Optional[str] = PydanticField(None, max_length=500)
    poster_url: Optional[HttpUrl] = None
    backdrop_url: Optional[HttpUrl] = None
    trailer_url: Optional[HttpUrl] = None
    imdb_rating: Optional[float] = PydanticField(None, ge=0, le=10)
    kinopoisk_rating: Optional[float] = PydanticField(None, ge=0, le=10)
    is_featured: Optional[bool] = None
    is_popular: Optional[bool] = None
    is_new: Optional[bool] = None
    is_available: Optional[bool] = None
    requires_subscription: Optional[bool] = None


class ContentResponse(ContentBase):
    """Ответ с контентом"""
    id: int
    uuid: str
    poster_url: Optional[HttpUrl]
    backdrop_url: Optional[HttpUrl]
    trailer_url: Optional[HttpUrl]
    imdb_rating: Optional[float]
    kinopoisk_rating: Optional[float]
    our_rating: Optional[float]
    is_featured: bool
    is_popular: bool
    is_new: bool
    is_available: bool
    requires_subscription: bool
    views_count: int
    watch_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    available_from: datetime
    available_to: Optional[datetime]
    content_type: ContentTypeResponse
    age_rating: AgeRatingResponse


class ContentDetailResponse(ContentResponse):
    """Детальный ответ с контентом"""
    genres: List[GenreResponse] = []
    countries: List[CountryResponse] = []
    actors: List["ActorResponse"] = []
    seasons: List["SeasonResponse"] = []
    ratings_summary: "RatingsSummary"
    user_rating: Optional["RatingResponse"] = None
    in_watchlist: bool = False
    watch_progress: Optional[float] = None


class ContentFilters(BaseSchema):
    """Фильтры для контента"""
    query: Optional[str] = PydanticField(None, min_length=2, description="Поисковый запрос")
    content_type_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    country_ids: Optional[List[int]] = None
    age_rating_ids: Optional[List[int]] = None
    min_year: Optional[int] = PydanticField(None, ge=1888, description="Минимальный год")
    max_year: Optional[int] = PydanticField(None, le=2100, description="Максимальный год")
    min_rating: Optional[float] = PydanticField(None, ge=0, le=10, description="Минимальный рейтинг")
    max_duration: Optional[int] = PydanticField(None, ge=0, description="Максимальная длительность")
    featured_only: bool = False
    popular_only: bool = False
    new_only: bool = False
    available_only: bool = True
    subscription_only: Optional[bool] = None
    sort_by: str = PydanticField(default="popularity", description="Сортировка")
    sort_order: str = PydanticField(default="desc", description="Порядок сортировки")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed = ['popularity', 'rating', 'release_year', 'title', 'created_at']
        if v not in allowed:
            raise ValueError(f'sort_by должен быть одним из: {allowed}')
        return v


# ============ АКТЕРЫ ============

class ActorBase(BaseSchema):
    """Базовая схема актера"""
    full_name: str = PydanticField(..., max_length=200)
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    biography: Optional[str] = None
    photo_url: Optional[HttpUrl] = None
    imdb_id: Optional[str] = PydanticField(None, max_length=20)
    tmdb_id: Optional[str] = PydanticField(None, max_length=20)

    @validator('death_date')
    def validate_dates(cls, v, values):
        if 'birth_date' in values and values['birth_date'] and v:
            if v <= values['birth_date']:
                raise ValueError('Дата смерти должна быть после даты рождения')
        return v


class ActorCreate(ActorBase):
    """Создание актера"""
    pass


class ActorResponse(ActorBase):
    """Ответ с актером"""
    id: int
    popularity: float
    contents_count: int


# ============ СЕЗОНЫ И ЭПИЗОДЫ ============

class SeasonBase(BaseSchema):
    """Базовая схема сезона"""
    season_number: int = PydanticField(..., ge=1, description="Номер сезона")
    title: Optional[str] = PydanticField(None, max_length=255, description="Название сезона")
    description: Optional[str] = None
    release_year: Optional[int] = PydanticField(None, ge=1888, le=2100, description="Год выхода")
    poster_url: Optional[HttpUrl] = None
    episode_count: int = PydanticField(default=0, ge=0, description="Количество эпизодов")


class SeasonCreate(SeasonBase):
    """Создание сезона"""
    content_id: int = PydanticField(..., description="ID контента")


class SeasonResponse(SeasonBase):
    """Ответ с сезоном"""
    id: int
    content_id: int
    episodes: List["EpisodeResponse"] = []


class EpisodeBase(BaseSchema):
    """Базовая схема эпизода"""
    episode_number: int = PydanticField(..., ge=1, description="Номер эпизода")
    title: str = PydanticField(..., max_length=255, description="Название эпизода")
    description: Optional[str] = None
    duration_minutes: int = PydanticField(default=0, ge=0, description="Длительность в минутах")
    video_quality_id: Optional[int] = None
    video_url: HttpUrl = PydanticField(..., description="URL видео")
    thumbnail_url: Optional[HttpUrl] = None
    preview_url: Optional[HttpUrl] = None
    director: Optional[str] = PydanticField(None, max_length=200)
    writer: Optional[str] = PydanticField(None, max_length=200)
    release_date: Optional[date] = None


class EpisodeCreate(EpisodeBase):
    """Создание эпизода"""
    season_id: int = PydanticField(..., description="ID сезона")
    content_id: int = PydanticField(..., description="ID контента")


class EpisodeResponse(EpisodeBase):
    """Ответ с эпизодом"""
    id: int
    uuid: str
    season_id: int
    content_id: int
    views_count: int
    video_quality: Optional[VideoQualityResponse]
    watch_progress: Optional[float] = None


# ============ МЕДИА ФАЙЛЫ ============

class MediaFileBase(BaseSchema):
    """Базовая схема медиа файла"""
    file_type: MediaType = MediaType.VIDEO
    file_url: HttpUrl
    file_size_bytes: Optional[int] = PydanticField(None, ge=0)
    duration_seconds: Optional[int] = PydanticField(None, ge=0)
    quality: Optional[str] = PydanticField(None, max_length=20)
    language: str = PydanticField(default="ru", max_length=10)
    is_main: bool = False


class MediaFileCreate(MediaFileBase):
    """Создание медиа файла"""
    content_id: Optional[int] = None
    episode_id: Optional[int] = None


class MediaFileResponse(MediaFileBase):
    """Ответ с медиа файлом"""
    id: int
    uuid: str
    content_id: Optional[int]
    episode_id: Optional[int]
    is_available: bool
    created_at: datetime


# ============ РЕЙТИНГИ И ОТЗЫВЫ ============

class RatingBase(BaseSchema):
    """Базовая схема рейтинга"""
    rating_value: float = PydanticField(..., ge=0.5, le=5.0, multiple_of=0.5, description="Оценка")
    review: Optional[str] = PydanticField(None, max_length=2000, description="Отзыв")
    is_public: bool = PydanticField(default=True, description="Публичный отзыв")


class RatingCreate(RatingBase):
    """Создание рейтинга"""
    content_id: int = PydanticField(..., description="ID контента")


class RatingUpdate(BaseSchema):
    """Обновление рейтинга"""
    rating_value: Optional[float] = PydanticField(None, ge=0.5, le=5.0, multiple_of=0.5)
    review: Optional[str] = PydanticField(None, max_length=2000)
    is_public: Optional[bool] = None


class RatingResponse(RatingBase):
    """Ответ с рейтингом"""
    id: int
    user_id: int
    content_id: int
    user: "UserShortResponse"
    likes_count: int
    created_at: datetime
    updated_at: Optional[datetime]


class RatingsSummary(BaseSchema):
    """Сводка по рейтингам"""
    total_ratings: int
    average_rating: float
    rating_distribution: Dict[str, int]
    review_count: int
    last_rating_date: Optional[datetime]


class HelpfulVoteCreate(BaseSchema):
    """Оценка полезности отзыва"""
    is_helpful: bool = PydanticField(default=True, description="Полезный отзыв")


# ============ ИСТОРИЯ ПРОСМОТРОВ ============

class WatchHistoryBase(BaseSchema):
    """Базовая схема истории просмотров"""
    watch_duration_seconds: int = PydanticField(default=0, ge=0, description="Продолжительность просмотра в секундах")
    progress_percentage: float = PydanticField(default=0.0, ge=0, le=100, description="Процент просмотра")
    is_completed: bool = PydanticField(default=False, description="Просмотр завершен")
    device_type: Optional[str] = PydanticField(None, max_length=50, description="Тип устройства")


class WatchHistoryCreate(WatchHistoryBase):
    """Создание записи истории просмотров"""
    content_id: int = PydanticField(..., description="ID контента")
    episode_id: Optional[int] = PydanticField(None, description="ID эпизода (для сериалов)")


class WatchHistoryResponse(WatchHistoryBase):
    """Ответ с историей просмотров"""
    id: int
    user_id: int
    content_id: int
    episode_id: Optional[int]
    watched_at: datetime
    content: "ContentShortResponse"
    episode: Optional["EpisodeShortResponse"]


class ContinueWatchingResponse(BaseSchema):
    """Продолжить просмотр"""
    content: "ContentShortResponse"
    episode: Optional["EpisodeShortResponse"]
    progress_percentage: float
    watch_duration_seconds: int
    last_watched_at: datetime


# ============ ЗАКЛАДКИ ============

class WatchlistBase(BaseSchema):
    """Базовая схема закладок"""
    priority: int = PydanticField(default=0, ge=0, le=10, description="Приоритет")
    notes: Optional[str] = PydanticField(None, max_length=500, description="Заметки")


class WatchlistCreate(WatchlistBase):
    """Добавление в закладки"""
    content_id: int = PydanticField(..., description="ID контента")


class WatchlistUpdate(BaseSchema):
    """Обновление закладки"""
    priority: Optional[int] = PydanticField(None, ge=0, le=10)
    notes: Optional[str] = PydanticField(None, max_length=500)


class WatchlistResponse(WatchlistBase):
    """Ответ с закладкой"""
    id: int
    user_id: int
    content_id: int
    added_at: datetime
    content: "ContentShortResponse"


# ============ КОРОТКИЕ ВЕРСИИ ============

class UserShortResponse(BaseSchema):
    """Короткая версия пользователя"""
    id: int
    username: str
    full_name: Optional[str]
    avatar_url: Optional[HttpUrl]


class ContentShortResponse(BaseSchema):
    """Короткая версия контента"""
    id: int
    title: str
    poster_url: Optional[HttpUrl]
    content_type: ContentTypeResponse
    duration_minutes: int
    release_year: int


class EpisodeShortResponse(BaseSchema):
    """Короткая версия эпизода"""
    id: int
    episode_number: int
    title: str
    duration_minutes: int
    thumbnail_url: Optional[HttpUrl]


# ============ АУТЕНТИФИКАЦИЯ ============

class LoginRequest(BaseSchema):
    """Запрос на вход"""
    username: str = PydanticField(..., description="Имя пользователя или email")
    password: str = PydanticField(..., description="Пароль")
    remember_me: bool = PydanticField(default=False, description="Запомнить меня")


class TokenResponse(BaseSchema):
    """Ответ с токеном"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user: UserResponse


class RefreshTokenRequest(BaseSchema):
    """Запрос на обновление токена"""
    refresh_token: str = PydanticField(..., description="Refresh token")


class PasswordResetRequest(BaseSchema):
    """Запрос на сброс пароля"""
    email: EmailStr = PydanticField(..., description="Email для сброса пароля")


class PasswordResetConfirm(BaseSchema):
    """Подтверждение сброса пароля"""
    token: str = PydanticField(..., description="Токен сброса пароля")
    new_password: str = PydanticField(..., min_length=8, description="Новый пароль")
    confirm_password: str = PydanticField(..., description="Подтверждение пароля")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Пароли не совпадают')
        return v


class EmailVerificationRequest(BaseSchema):
    """Запрос на верификацию email"""
    token: str = PydanticField(..., description="Токен верификации")


# ============ АНАЛИТИКА ============

class AnalyticsFilters(BaseSchema):
    """Фильтры для аналитики"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    group_by: str = PydanticField(default="day", description="Группировка: day, week, month")
    content_type_id: Optional[int] = None
    age_rating_id: Optional[int] = None

    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and values['start_date'] and v:
            if v < values['start_date']:
                raise ValueError('Дата окончания должна быть после даты начала')
        return v


class PopularContentResponse(BaseSchema):
    """Популярный контент"""
    content: ContentShortResponse
    views: int
    watch_time_minutes: int
    average_rating: Optional[float]
    completion_rate: float


class UserActivityResponse(BaseSchema):
    """Активность пользователей"""
    period: Dict[str, datetime]
    new_users: int
    active_users: int
    returning_users: int
    total_watch_hours: float
    average_watch_time_per_user: float
    most_popular_content: List[PopularContentResponse]


class DailyStats(BaseSchema):
    """Ежедневная статистика"""
    date: date
    new_users: int
    active_users: int
    watch_time_minutes: int
    new_content: int
    new_ratings: int


# ============ ПЛАТЕЖИ И ПОДПИСКИ ============

class PaymentCreate(BaseSchema):
    """Создание платежа"""
    subscription_tier_id: int = PydanticField(..., description="ID тарифа подписки")
    payment_method: str = PydanticField(..., max_length=50, description="Метод оплаты")
    amount: float = PydanticField(..., ge=0, description="Сумма")
    currency: str = PydanticField(default="RUB", max_length=3, description="Валюта")
    description: Optional[str] = PydanticField(None, description="Описание")


class PaymentResponse(BaseSchema):
    """Ответ с платежом"""
    id: int
    uuid: str
    user_id: int
    subscription_tier_id: int
    amount: float
    currency: str
    status: str
    payment_method: str
    payment_gateway: str
    gateway_transaction_id: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    paid_at: Optional[datetime]


class SubscriptionCreate(BaseSchema):
    """Создание подписки"""
    subscription_tier_id: int = PydanticField(..., description="ID тарифа подписки")
    auto_renew: bool = PydanticField(default=True, description="Автопродление")


class SubscriptionResponse(BaseSchema):
    """Ответ с подпиской"""
    id: int
    user_id: int
    subscription_tier: SubscriptionTierResponse
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    auto_renew: bool
    created_at: datetime


# ============ СПРАВОЧНЫЕ ДАННЫЕ ============

class ReferenceData(BaseSchema):
    """Все справочники"""
    content_types: List[ContentTypeResponse]
    age_ratings: List[AgeRatingResponse]
    subscription_tiers: List[SubscriptionTierResponse]
    video_qualities: List[VideoQualityResponse]
    genres: List[GenreResponse]
    countries: List[CountryResponse]


# ============ УТИЛИТЫ ============

class SuccessResponse(BaseSchema):
    """Успешный ответ"""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseSchema):
    """Ответ с ошибкой"""
    success: bool = False
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None


class ValidationErrorResponse(BaseSchema):
    """Ошибка валидации"""
    success: bool = False
    error: str = "Validation Error"
    details: List[Dict[str, Any]]


# ============ ПОИСК ============

class SearchRequest(BaseSchema):
    """Запрос поиска"""
    query: str = PydanticField(..., min_length=2, description="Поисковый запрос")
    content_type_id: Optional[int] = None
    genre_id: Optional[int] = None
    year: Optional[int] = None
    limit: int = PydanticField(default=20, le=100)
    offset: int = 0


class SearchResponse(BaseSchema):
    """Ответ поиска"""
    query: str
    total: int
    results: List[ContentResponse]
    facets: Dict[str, Any]


# ============ РЕКОМЕНДАЦИИ ============

class RecommendationRequest(BaseSchema):
    """Запрос рекомендаций"""
    limit: int = PydanticField(default=10, le=50)
    based_on: Optional[str] = PydanticField(
        default="history",
        description="Основа: history, ratings, watchlist, popular"
    )
    content_type_id: Optional[int] = None
    exclude_watched: bool = True


class RecommendationResponse(BaseSchema):
    """Ответ с рекомендациями"""
    based_on: str
    content: List[ContentResponse]
    reason: Optional[str] = None


# Автоматическое обновление forward references
ContentDetailResponse.update_forward_refs()
SeasonResponse.update_forward_refs()
RatingResponse.update_forward_refs()
WatchHistoryResponse.update_forward_refs()
ContinueWatchingResponse.update_forward_refs()
WatchlistResponse.update_forward_refs()