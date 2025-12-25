"""
Скрипт для заполнения БД тестовыми данными
"""

import asyncio
from sqlmodel import Session, select
from faker import Faker
import random
from datetime import datetime, timedelta

from database import engine, get_session
import models
import schemas

fake = Faker("ru_RU")


async def seed_users(count: int = 100):
    """Заполнение пользователей"""
    with Session(engine) as session:
        # Проверяем, есть ли уже пользователи
        existing = session.exec(select(models.User).limit(1)).first()
        if existing:
            print("Пользователи уже существуют")
            return

        print(f"Создание {count} пользователей...")

        for i in range(count):
            user = models.User(
                email=fake.unique.email(),
                username=fake.unique.user_name(),
                hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
                full_name=fake.name(),
                subscription_tier_id=random.choice([1, 2, 3, 4]),
                is_verified=random.choice([True, False]),
                is_staff=True if i < 5 else False,
                is_superuser=True if i == 0 else False,
                created_at=fake.date_time_between(start_date="-1y", end_date="now"),
                last_login=fake.date_time_between(start_date="-30d", end_date="now") if random.random() > 0.3 else None
            )
            session.add(user)

        session.commit()
        print("✅ Пользователи созданы")


async def seed_actors(count: int = 50):
    """Заполнение актеров"""
    with Session(engine) as session:
        existing = session.exec(select(models.Actor).limit(1)).first()
        if existing:
            print("Актеры уже существуют")
            return

        print(f"Создание {count} актеров...")

        for _ in range(count):
            actor = models.Actor(
                full_name=fake.name(),
                birth_date=fake.date_of_birth(minimum_age=20, maximum_age=80),
                death_date=fake.date_of_birth(minimum_age=0, maximum_age=20) if random.random() > 0.8 else None,
                biography=fake.text(max_nb_chars=500),
                photo_url=fake.image_url(),
                popularity=random.uniform(0, 100)
            )
            session.add(actor)

        session.commit()
        print("✅ Актеры созданы")


async def seed_content(count: int = 200):
    """Заполнение контента"""
    with Session(engine) as session:
        existing = session.exec(select(models.Content).limit(1)).first()
        if existing:
            print("Контент уже существует")
            return

        # Получаем справочники
        content_types = session.exec(select(models.ContentType)).all()
        age_ratings = session.exec(select(models.AgeRating)).all()
        genres = session.exec(select(models.Genre)).all()
        countries = session.exec(select(models.Country)).all()
        actors = session.exec(select(models.Actor)).all()

        print(f"Создание {count} единиц контента...")

        for i in range(count):
            content_type = random.choice(content_types)
            is_series = content_type.code == "series"

            content = models.Content(
                title=fake.catch_phrase(),
                original_title=fake.catch_phrase() if random.random() > 0.5 else None,
                description=fake.text(max_nb_chars=1000),
                short_description=fake.sentence(),
                content_type_id=content_type.id,
                age_rating_id=random.choice(age_ratings).id,
                release_year=random.randint(1950, 2024),
                duration_minutes=random.randint(60, 180) if not is_series else None,
                director=fake.name(),
                writer=fake.name() if random.random() > 0.3 else None,
                imdb_id=f"tt{random.randint(1000000, 9999999)}",
                poster_url=fake.image_url(width=400, height=600),
                backdrop_url=fake.image_url(width=1920, height=1080),
                trailer_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                imdb_rating=round(random.uniform(5.0, 9.5), 1),
                kinopoisk_rating=round(random.uniform(5.0, 9.5), 1) if random.random() > 0.3 else None,
                our_rating=round(random.uniform(5.0, 9.5), 1) if random.random() > 0.5 else None,
                is_featured=random.random() > 0.7,
                is_popular=random.random() > 0.8,
                is_new=random.random() > 0.9,
                is_available=True,
                requires_subscription=random.random() > 0.3,
                created_at=fake.date_time_between(start_date="-1y", end_date="now"),
                available_from=datetime.utcnow() - timedelta(days=random.randint(0, 365)),
                available_to=datetime.utcnow() + timedelta(
                    days=random.randint(0, 365)) if random.random() > 0.5 else None,
                views_count=random.randint(0, 10000),
                watch_count=random.randint(0, 5000)
            )
            session.add(content)
            session.flush()  # Получаем ID

            # Добавляем жанры (2-4 жанра на контент)
            for _ in range(random.randint(2, 4)):
                genre = random.choice(genres)
                session.add(models.ContentGenre(
                    content_id=content.id,
                    genre_id=genre.id
                ))

            # Добавляем страны (1-3 страны)
            for _ in range(random.randint(1, 3)):
                country = random.choice(countries)
                session.add(models.ContentCountry(
                    content_id=content.id,
                    country_id=country.id
                ))

            # Добавляем актеров (3-10 актеров)
            for j in range(random.randint(3, 10)):
                actor = random.choice(actors)
                session.add(models.ContentActor(
                    content_id=content.id,
                    actor_id=actor.id,
                    role=fake.job() if random.random() > 0.5 else None,
                    is_main=j < 3  # Первые 3 актера - главные
                ))

            # Для сериалов создаем сезоны и эпизоды
            if is_series:
                seasons_count = random.randint(1, 5)
                for season_num in range(1, seasons_count + 1):
                    season = models.Season(
                        content_id=content.id,
                        season_number=season_num,
                        title=f"Сезон {season_num}",
                        description=fake.text(max_nb_chars=200),
                        release_year=content.release_year + season_num - 1,
                        episode_count=random.randint(6, 12)
                    )
                    session.add(season)
                    session.flush()

                    # Создаем эпизоды для сезона
                    episodes_count = random.randint(6, 12)
                    for ep_num in range(1, episodes_count + 1):
                        episode = models.Episode(
                            season_id=season.id,
                            content_id=content.id,
                            episode_number=ep_num,
                            title=f"Эпизод {ep_num}: {fake.catch_phrase()}",
                            description=fake.text(max_nb_chars=300),
                            duration_minutes=random.randint(40, 60),
                            video_url="https://storage.example.com/videos/episode.mp4",
                            thumbnail_url=fake.image_url(),
                            release_date=fake.date_between(
                                start_date=f"-{season_num}y",
                                end_date="today"
                            )
                        )
                        session.add(episode)

        session.commit()
        print("✅ Контент создан")


async def seed_ratings():
    """Заполнение рейтингов"""
    with Session(engine) as session:
        existing = session.exec(select(models.Rating).limit(1)).first()
        if existing:
            print("Рейтинги уже существуют")
            return

        # Получаем пользователей и контент
        users = session.exec(select(models.User)).all()
        content_list = session.exec(select(models.Content)).all()

        print("Создание рейтингов...")

        for user in users:
            # Каждый пользователь оценивает 5-20 случайных фильмов
            rated_content = random.sample(content_list, min(len(content_list), random.randint(5, 20)))

            for content in rated_content:
                rating = models.Rating(
                    user_id=user.id,
                    content_id=content.id,
                    rating_value=random.choice([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]),
                    review=fake.text(max_nb_chars=200) if random.random() > 0.7 else None,
                    is_public=random.random() > 0.2,
                    created_at=fake.date_time_between(start_date="-180d", end_date="now")
                )
                session.add(rating)

        session.commit()
        print("✅ Рейтинги созданы")


async def seed_watchlist():
    """Заполнение закладок"""
    with Session(engine) as session:
        existing = session.exec(select(models.Watchlist).limit(1)).first()
        if existing:
            print("Закладки уже существуют")
            return

        users = session.exec(select(models.User)).all()
        content_list = session.exec(select(models.Content)).all()

        print("Создание закладок...")

        for user in users:
            # Каждый пользователь добавляет 3-10 фильмов в закладки
            watchlist_content = random.sample(content_list, min(len(content_list), random.randint(3, 10)))

            for content in watchlist_content:
                watchlist = models.Watchlist(
                    user_id=user.id,
                    content_id=content.id,
                    priority=random.randint(0, 10),
                    notes=fake.sentence() if random.random() > 0.8 else None,
                    added_at=fake.date_time_between(start_date="-90d", end_date="now")
                )
                session.add(watchlist)

        session.commit()
        print("✅ Закладки созданы")


async def seed_watch_history():
    """Заполнение истории просмотров"""
    with Session(engine) as session:
        existing = session.exec(select(models.WatchHistory).limit(1)).first()
        if existing:
            print("История просмотров уже существует")
            return

        users = session.exec(select(models.User)).all()
        content_list = session.exec(select(models.Content)).all()

        print("Создание истории просмотров...")

        for user in users:
            # Каждый пользователь смотрел 10-50 фильмов
            watched_content = random.sample(content_list, min(len(content_list), random.randint(10, 50)))

            for content in watched_content:
                # Для каждого просмотренного контента создаем 1-5 записей
                for _ in range(random.randint(1, 5)):
                    is_completed = random.random() > 0.3
                    progress = 100 if is_completed else random.randint(10, 90)

                    history = models.WatchHistory(
                        user_id=user.id,
                        content_id=content.id,
                        episode_id=None,  # Для упрощения
                        watched_at=fake.date_time_between(start_date="-180d", end_date="now"),
                        watch_duration_seconds=random.randint(300,
                                                              content.duration_minutes * 60) if content.duration_minutes else random.randint(
                            300, 7200),
                        progress_percentage=progress,
                        is_completed=is_completed,
                        device_type=random.choice(["web", "android", "ios", "smart_tv"])
                    )
                    session.add(history)

        session.commit()
        print("✅ История просмотров создана")


async def main():
    """Основная функция заполнения БД"""
    print("🚀 Начало заполнения БД тестовыми данными...")

    await seed_users(50)
    await seed_actors(30)
    await seed_content(100)
    await seed_ratings()
    await seed_watchlist()
    await seed_watch_history()

    print("🎉 Заполнение БД завершено!")


if __name__ == "__main__":
    asyncio.run(main())