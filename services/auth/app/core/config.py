from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    SERVICE_NAME: str = Field(default="auth-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")

    RELOAD: bool = Field(default=False, description="Auto-reload on code changes")
    WORKERS: int = Field(default=1, description="Number of worker processes")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8001)

    POSTGRES_USER: str = Field(default="auth_user")
    POSTGRES_PASSWORD: str = Field(default="auth_password")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="auth_db")

    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0)

    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production-min-32-chars-please")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    LOGIN_RATE_LIMIT_PER_MINUTE: int = Field(default=5)
    LOGIN_RATE_LIMIT_PER_HOUR: int = Field(default=20)

    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    JSON_LOGS: bool = Field(default=True, description="Enable JSON logging")


    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()