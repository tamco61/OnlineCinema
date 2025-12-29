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

    SERVICE_NAME: str = Field(default="streaming-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")
    HOST: str = Field(default="localhost")
    PORT: int = Field(default=8005)

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "streaming_service"
    POSTGRES_PASSWORD: str = "streaming_password"
    POSTGRES_DB: str = "streaming_db"

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL DSN."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() == "development"

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()