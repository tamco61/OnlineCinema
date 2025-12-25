"""
Настройка базы данных и сессий
"""

from sqlmodel import SQLModel, Session, create_engine, select
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, Optional
import logging
from config import settings

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем движок базы данных
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_recycle=settings.database_pool_recycle,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)


def create_db_and_tables():
    """
    Создание таблиц в базе данных
    """
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("✅ Таблицы базы данных созданы")

        # Инициализируем начальные данные
        init_reference_data()
        logger.info("✅ Начальные данные инициализированы")

    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблиц: {e}")
        raise


def get_engine():
    """Получить движок базы данных"""
    return engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Контекстный менеджер для получения сессии БД

    Использование:
    ```python
    with get_session() as session:
        # Работа с БД
        user = session.get(User, 1)
    ```
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка в сессии БД: {e}")
        raise
    finally:
        session.close()


def init_reference_data():
    """
    Инициализация справочных данных
    """
    from models import (
        ContentType, AgeRating, SubscriptionTier,
        SubscriptionFeature, VideoQuality, Genre, Country
    )

    with get_session() as session:
        # Типы контента
        if not session.exec(select(ContentType).limit(1)).first():
            content_types = [
                ContentType(code="movie", name="Фильм", sort_order=1),
                ContentType(code="series", name="Сериал", sort_order=2),
                ContentType(code="documentary", name="Документальный", sort_order=3),
                ContentType(code="animation", name="Анимация", sort_order=4),
                ContentType(code="short", name="Короткометражка", sort_order=5),
                ContentType(code="tv_show", name="ТВ-шоу", sort_order=6),
            ]
            for ct in content_types:
                session.add(ct)

        # Возрастные рейтинги
        if not session.exec(select(AgeRating).limit(1)).first():
            age_ratings = [
                AgeRating(code="G", name="Для всех возрастов", min_age=0),
                AgeRating(code="PG", name="Детям с родителями", min_age=7),
                AgeRating(code="PG-13", name="С 13 лет", min_age=13),
                AgeRating(code="R", name="С 17 лет", min_age=17),
                AgeRating(code="NC-17", name="Только с 18 лет", min_age=18),
            ]
            for ar in age_ratings:
                session.add(ar)

        # Тарифы подписки
        if not session.exec(select(SubscriptionTier).limit(1)).first():
            tiers_data = [
                {
                    "code": "free",
                    "name": "Бесплатный",
                    "price_monthly": 0,
                    "price_yearly": 0,
                    "max_simultaneous_streams": 1,
                    "max_video_quality": "HD",
                    "features": ["Реклама", "Только HD качество", "Базовый контент"]
                },
                {
                    "code": "basic",
                    "name": "Базовый",
                    "price_monthly": 299,
                    "price_yearly": 2990,
                    "max_simultaneous_streams": 2,
                    "max_video_quality": "FullHD",
                    "features": ["Без рекламы", "FullHD качество", "2 устройства", "Все фильмы"]
                },
                {
                    "code": "premium",
                    "name": "Премиум",
                    "price_monthly": 599,
                    "price_yearly": 5990,
                    "max_simultaneous_streams": 4,
                    "max_video_quality": "4K",
                    "features": [
                        "Без рекламы",
                        "4K качество",
                        "4 устройства",
                        "Все фильмы и сериалы",
                        "Оффлайн-просмотр",
                        "Ранний доступ",
                        "Персональные рекомендации"
                    ]
                },
                {
                    "code": "family",
                    "name": "Семейный",
                    "price_monthly": 899,
                    "price_yearly": 8990,
                    "max_simultaneous_streams": 6,
                    "max_video_quality": "4K",
                    "features": [
                        "Без рекламы",
                        "4K качество",
                        "6 устройств",
                        "Все фильмы и сериалы",
                        "Оффлайн-просмотр",
                        "Детский режим",
                        "Разные профили"
                    ]
                }
            ]

            for tier_data in tiers_data:
                tier = SubscriptionTier(
                    code=tier_data["code"],
                    name=tier_data["name"],
                    price_monthly=tier_data["price_monthly"],
                    price_yearly=tier_data.get("price_yearly"),
                    max_simultaneous_streams=tier_data["max_simultaneous_streams"],
                    max_video_quality=tier_data["max_video_quality"]
                )
                session.add(tier)
                session.flush()  # Получаем ID

                # Добавляем фичи
                for i, feature in enumerate(tier_data["features"]):
                    session.add(SubscriptionFeature(
                        tier_id=tier.id,
                        feature=feature,
                        sort_order=i
                    ))

        # Качество видео
        if not session.exec(select(VideoQuality).limit(1)).first():
            qualities = [
                VideoQuality(code="240p", name="240p", width=426, height=240, bitrate=400, sort_order=1),
                VideoQuality(code="360p", name="360p", width=640, height=360, bitrate=800, sort_order=2),
                VideoQuality(code="480p", name="480p", width=854, height=480, bitrate=1200, sort_order=3),
                VideoQuality(code="720p", name="HD", width=1280, height=720, bitrate=2500, sort_order=4),
                VideoQuality(code="1080p", name="Full HD", width=1920, height=1080, bitrate=5000, sort_order=5),
                VideoQuality(code="1440p", name="2K", width=2560, height=1440, bitrate=8000, sort_order=6),
                VideoQuality(code="2160p", name="4K", width=3840, height=2160, bitrate=15000, sort_order=7),
            ]
            for q in qualities:
                session.add(q)

        # Жанры
        if not session.exec(select(Genre).limit(1)).first():
            genres = [
                Genre(name="Боевик"),
                Genre(name="Комедия"),
                Genre(name="Драма"),
                Genre(name="Фантастика"),
                Genre(name="Фэнтези"),
                Genre(name="Ужасы"),
                Genre(name="Триллер"),
                Genre(name="Детектив"),
                Genre(name="Мелодрама"),
                Genre(name="Приключения"),
                Genre(name="Исторический"),
                Genre(name="Биография"),
                Genre(name="Вестерн"),
                Genre(name="Военный"),
                Genre(name="Мюзикл"),
                Genre(name="Спорт"),
                Genre(name="Документальный"),
                Genre(name="Аниме"),
                Genre(name="Семейный"),
                Genre(name="Криминал"),
            ]
            for genre in genres:
                session.add(genre)

        # Страны
        if not session.exec(select(Country).limit(1)).first():
            countries = [
                Country(code="RU", name="Россия", name_en="Russia"),
                Country(code="US", name="США", name_en="United States"),
                Country(code="GB", name="Великобритания", name_en="United Kingdom"),
                Country(code="FR", name="Франция", name_en="France"),
                Country(code="DE", name="Германия", name_en="Germany"),
                Country(code="IT", name="Италия", name_en="Italy"),
                Country(code="ES", name="Испания", name_en="Spain"),
                Country(code="JP", name="Япония", name_en="Japan"),
                Country(code="KR", name="Корея", name_en="South Korea"),
                Country(code="CN", name="Китай", name_en="China"),
                Country(code="IN", name="Индия", name_en="India"),
                Country(code="BR", name="Бразилия", name_en="Brazil"),
                Country(code="CA", name="Канада", name_en="Canada"),
                Country(code="AU", name="Австралия", name_en="Australia"),
            ]
            for country in countries:
                session.add(country)


# Функции для работы с БД
def get_or_create(session, model, defaults=None, **kwargs):
    """
    Получить или создать объект

    Пример:
    ```python
    user = get_or_create(session, User, email="test@example.com")
    ```
    """
    instance = session.exec(select(model).filter_by(**kwargs)).first()
    if instance:
        return instance, False

    params = kwargs.copy()
    if defaults:
        params.update(defaults)

    instance = model(**params)
    session.add(instance)
    session.flush()
    return instance, True


def bulk_create(session, model, data_list):
    """
    Массовое создание объектов

    Пример:
    ```python
    users_data = [{"email": f"user{i}@example.com"} for i in range(10)]
    bulk_create(session, User, users_data)
    ```
    """
    instances = [model(**data) for data in data_list]
    session.add_all(instances)
    session.flush()
    return instances


# Утилиты для работы с JSON
import json
from sqlalchemy import TypeDecorator, Text
from sqlalchemy.ext.mutable import MutableDict


class JSONEncodedDict(TypeDecorator):
    """Кастомный тип для хранения JSON в БД"""
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value, ensure_ascii=False)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


# Экспортируем типы
JSONType = JSONEncodedDict().with_variant(Text, "sqlite")