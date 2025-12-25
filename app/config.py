"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # ============ БАЗА ДАННЫХ ============
    database_url: str = "sqlite:///./cinema.db"
    database_pool_size: int = 20
    database_max_overflow: int = 30
    database_pool_recycle: int = 3600
    database_echo: bool = False

    # ============ JWT И БЕЗОПАСНОСТЬ ============
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ============ НАСТРОЙКИ ПРИЛОЖЕНИЯ ============
    debug: bool = False
    app_name: str = "Онлайн-кинотеатр API"
    version: str = "2.0.0"
    api_prefix: str = "/api/v1"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # ============ ДОПОЛНИТЕЛЬНЫЕ ============
    redis_url: str = "redis://localhost:6379"
    log_level: str = "INFO"

    # ============ ПРЕДНАСТРОЙКИ ============
    default_subscription_tier_id: int = 1
    default_content_type_id: int = 1
    default_age_rating_id: int = 3

    # ============ ПУТИ К ФАЙЛАМ ============
    upload_dir: str = "./uploads"
    static_dir: str = "./static"
    logs_dir: str = "./logs"

    # ============ ЛИМИТЫ ============
    max_file_size_mb: int = 100
    max_requests_per_minute: int = 60
    password_min_length: int = 8

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Кэшируем настройки для быстрого доступа
    """
    return Settings()


settings = get_settings()