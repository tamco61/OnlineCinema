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

    SERVICE_NAME: str = Field(default="search-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")
    OTEL_COLLECTOR_ENDPOINT: str = Field(default="http://otel-collector:4318")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8004)
    DEBUG: bool = False

    ELASTICSEARCH_HOSTS: list[str] = ["http://localhost:9200"]
    ELASTICSEARCH_INDEX: str = "movies"
    ELASTICSEARCH_TIMEOUT: int = 30
    ELASTICSEARCH_MAX_RETRIES: int = 3

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_PREFIX: str = "catalog"
    KAFKA_CONSUMER_GROUP: str = "search-service"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    ENABLE_KAFKA: bool = True

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 2
    REDIS_PASSWORD: str | None = None
    REDIS_CACHE_TTL: int = 300
    ENABLE_CACHE: bool = True

    SEARCH_DEFAULT_PAGE_SIZE: int = 20
    SEARCH_MAX_PAGE_SIZE: int = 100
    AUTOCOMPLETE_MAX_SUGGESTIONS: int = 10

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
