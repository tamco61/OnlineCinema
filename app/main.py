"""
Главное приложение FastAPI онлайн-кинотеатра
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import uvicorn
import logging
import time
import os
from pathlib import Path

from config import settings
from database import create_db_and_tables, engine
import dependencies
from routers import (
    auth, users, content, ratings,
    watchlist, analytics, references
)
import schemas

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"{settings.logs_dir}/app.log")
    ]
)

logger = logging.getLogger(__name__)

# Создаем необходимые директории
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.static_dir, exist_ok=True)
os.makedirs(settings.logs_dir, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan менеджер приложения

    - При запуске: создаем таблицы БД
    - При завершении: закрываем соединения
    """
    # Старт приложения
    logger.info("🚀 Запуск онлайн-кинотеатра...")
    logger.info(f"📊 Режим: {'development' if settings.debug else 'production'}")
    logger.info(f"🗄️  База данных: {settings.database_url}")

    try:
        create_db_and_tables()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise

    yield

    # Завершение приложения
    logger.info("👋 Завершение работы онлайн-кинотеатра...")
    engine.dispose()
    logger.info("✅ Соединения с БД закрыты")


# Создаем приложение FastAPI
app = FastAPI(
    title=settings.app_name,
    description="""
    🎬 **Онлайн-кинотеатр API**

    Полноценный REST API для стримингового сервиса с поддержкой:

    - 📺 Фильмы и сериалы
    - ⭐ Рейтинги и отзывы
    - 📋 Закладки и история просмотров
    - 👥 Управление пользователями
    - 💳 Подписки и платежи
    - 📊 Аналитика и статистика

    ## Аутентификация

    Большинство эндпоинтов требуют JWT аутентификации.

    1. Зарегистрируйтесь через `/auth/register`
    2. Получите токен через `/auth/login`
    3. Используйте токен в заголовке `Authorization: Bearer <token>`

    ## Документация

    - **Swagger UI**: [/docs](/docs)
    - **ReDoc**: [/redoc](/redoc)
    - **OpenAPI**: [/openapi.json](/openapi.json)
    """,
    version=settings.version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
    dependencies=[Depends(dependencies.validate_pagination_params)]
)

# ============ MIDDLEWARE ============

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Trusted hosts middleware
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # В продакшене заменить на конкретные хосты
    )

# GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Логирование запросов middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware для логирования запросов
    """
    start_time = time.time()

    # Логируем входящий запрос
    logger.info(
        f"📥 {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    try:
        response = await call_next(request)

        # Логируем ответ
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"📤 {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.2f}ms"
        )

        # Добавляем время обработки в заголовки
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        return response

    except Exception as e:
        # Логируем ошибки
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"❌ {request.method} {request.url.path} - "
            f"Error: {str(e)} - "
            f"Time: {process_time:.2f}ms"
        )
        raise


# ============ ОБРАБОТЧИКИ ОШИБОК ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Обработчик HTTP исключений
    """
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail} - "
        f"{request.method} {request.url.path}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=schemas.ErrorResponse(
            success=False,
            error=exc.detail,
            code=f"HTTP_{exc.status_code}"
        ).dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Обработчик ошибок валидации
    """
    logger.warning(
        f"Validation error: {exc.errors()} - "
        f"{request.method} {request.url.path}"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=schemas.ValidationErrorResponse(
            success=False,
            details=exc.errors()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Обработчик общих исключений
    """
    logger.error(
        f"Unhandled exception: {str(exc)} - "
        f"{request.method} {request.url.path}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=schemas.ErrorResponse(
            success=False,
            error="Внутренняя ошибка сервера",
            code="INTERNAL_SERVER_ERROR",
            details={"message": str(exc)} if settings.debug else None
        ).dict()
    )


# ============ СТАТИЧЕСКИЕ ФАЙЛЫ ============

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# ============ ПОДКЛЮЧЕНИЕ РОУТЕРОВ ============

# API роутеры
app.include_router(
    auth.router,
    prefix=f"{settings.api_prefix}/auth",
    tags=["Аутентификация"]
)

app.include_router(
    users.router,
    prefix=f"{settings.api_prefix}/users",
    tags=["Пользователи"]
)

app.include_router(
    content.router,
    prefix=f"{settings.api_prefix}/content",
    tags=["Контент"]
)

app.include_router(
    ratings.router,
    prefix=f"{settings.api_prefix}/ratings",
    tags=["Рейтинги"]
)

app.include_router(
    watchlist.router,
    prefix=f"{settings.api_prefix}/watchlist",
    tags=["Закладки"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.api_prefix}/analytics",
    tags=["Аналитика"]
)

app.include_router(
    references.router,
    prefix=f"{settings.api_prefix}/references",
    tags=["Справочники"]
)


# ============ ОСНОВНЫЕ ЭНДПОИНТЫ ============

@app.get("/")
async def root():
    """
    Корневой эндпоинт
    """
    return schemas.SuccessResponse(
        message="🎬 Добро пожаловать в API онлайн-кинотеатра!",
        data={
            "name": settings.app_name,
            "version": settings.version,
            "docs": "/docs",
            "api_prefix": settings.api_prefix,
            "endpoints": {
                "auth": f"{settings.api_prefix}/auth",
                "users": f"{settings.api_prefix}/users",
                "content": f"{settings.api_prefix}/content",
                "ratings": f"{settings.api_prefix}/ratings",
                "watchlist": f"{settings.api_prefix}/watchlist",
                "analytics": f"{settings.api_prefix}/analytics",
                "references": f"{settings.api_prefix}/references"
            }
        }
    )


@app.get("/health")
async def health_check():
    """
    Проверка здоровья приложения

    Проверяет:
    - Доступность приложения
    - Подключение к БД
    - Статус сервисов
    """
    from sqlmodel import text

    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # Проверка БД
    try:
        with dependencies.get_db() as session:
            session.exec(text("SELECT 1")).first()
            health_data["services"]["database"] = "connected"
    except Exception as e:
        health_data["services"]["database"] = "disconnected"
        health_data["status"] = "unhealthy"
        health_data["error"] = str(e)

    # Проверка других сервисов может быть добавлена здесь
    # (Redis, кэш, внешние API и т.д.)

    status_code = 200 if health_data["status"] == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content=health_data
    )


@app.get("/info")
async def app_info():
    """
    Информация о приложении
    """
    return {
        "name": settings.app_name,
        "version": settings.version,
        "description": "Онлайн-кинотеатр на FastAPI и SQLModel",
        "environment": "development" if settings.debug else "production",
        "database": settings.database_url.split("://")[0],
        "debug": settings.debug,
        "timezone": "UTC",
        "uptime": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
    }


# ============ КАСТОМНАЯ OpenAPI СХЕМА ============

def custom_openapi():
    """
    Кастомизация OpenAPI схемы
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.version,
        description=app.description,
        routes=app.routes,
    )

    # Добавляем кастомные элементы
    openapi_schema["info"]["contact"] = {
        "name": "Техническая поддержка",
        "email": "support@cinema.example.com",
        "url": "https://cinema.example.com/support"
    }

    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }

    openapi_schema["info"]["x-logo"] = {
        "url": "https://cinema.example.com/logo.png",
        "altText": "Логотип онлайн-кинотеатра"
    }

    # Добавляем security схемы
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Введите JWT токен в формате: Bearer <token>"
        }
    }

    # Глобальные security требования
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Теги для группировки
    openapi_schema["tags"] = [
        {
            "name": "Аутентификация",
            "description": "Регистрация, вход, управление токенами"
        },
        {
            "name": "Пользователи",
            "description": "Управление пользователями и профилями"
        },
        {
            "name": "Контент",
            "description": "Фильмы, сериалы, эпизоды"
        },
        {
            "name": "Рейтинги",
            "description": "Оценки и отзывы"
        },
        {
            "name": "Закладки",
            "description": "Персональные списки просмотра"
        },
        {
            "name": "Аналитика",
            "description": "Статистика и метрики"
        },
        {
            "name": "Справочники",
            "description": "Управление справочными данными"
        }
    ]

    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi

# ============ ЗАПУСК ПРИЛОЖЕНИЯ ============

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
        workers=1 if settings.debug else 4
    )