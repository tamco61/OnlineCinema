from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    SERVICE_NAME: str = Field(default="user-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")
    HOST: str = Field(default="localhost")
    PORT: int = Field(default=8002)

    POSTGRES_USER: str = Field(default="user_service")
    POSTGRES_PASSWORD: str = Field(default="user_password")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="user_db")

    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: str | None = Field(default=None)
    REDIS_DB: int = Field(default=0)
    REDIS_CACHE_TTL: int = Field(default=300, description="Cache TTL in seconds")

    JWT_SECRET_KEY: str = Field(default="your-secret-key-must-match-auth-service")
    JWT_ALGORITHM: str = Field(default="HS256")

    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])

    LOG_LEVEL: str = Field(default="INFO")

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()