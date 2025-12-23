from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "postgres_db"
    POSTGRES_PORT: int = 5432

    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_ENDPOINT: str
    MINIO_BUCKET: str

    SECRET_KEY: str = "secret_jwt_key"
    ALGORITHM: str = "HS256"


settings = Settings()
