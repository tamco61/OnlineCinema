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

    SERVICE_NAME: str = Field(default="analytics-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")
    OTEL_COLLECTOR_ENDPOINT: str = Field(default="http://otel-collector:4318")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8006)
    DEBUG: bool = False

    # ClickHouse
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 9000
    CLICKHOUSE_HTTP_PORT: int = 8123
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""
    CLICKHOUSE_DATABASE: str = "analytics"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP: str = "analytics-service"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    ENABLE_KAFKA: bool = True

    # Analytics Settings
    DEFAULT_TIME_RANGE_DAYS: int = 7
    POPULAR_CONTENT_LIMIT: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()