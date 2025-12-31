
import uuid
from datetime import datetime

from fastapi import HTTPException, status, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.catalog.app.services.redis import RedisService, get_redis_service
from services.catalog.app.db.models import Genre, Movie, MoviePerson, Person, PersonRole
from services.catalog.app.schemas.movie import MovieCreate, MovieUpdate
from services.catalog.app.services.kafka import KafkaProducerService, get_kafka_producer
from services.catalog.app.db.session import get_db

from shared.utils.telemetry.tracer import trace_span


class MovieService:
    def __init__(
        self,
        db: AsyncSession,
        kafka: KafkaProducerService,
        redis: RedisService,
    ):
        self.db = db
        self.kafka = kafka
        self.redis = redis

    async def get_movies(
        self,
        page: int = 1,
        page_size: int = 20,
        published_only: bool = True,
        search: str | None = None,
    ) -> tuple[list[Movie], int]:
        with trace_span("movie.get_movies"):
            query = select(Movie)

            if published_only:
                query = query.where(Movie.is_published)

            if search:
                query = query.where(
                    or_(
                        Movie.title.ilike(f"%{search}%"),
                        Movie.description.ilike(f"%{search}%"),
                    )
                )

            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            query = (
                query.order_by(Movie.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )

            result = await self.db.execute(query)
            return list(result.scalars().all()), total

    async def get_movie_by_id(self, movie_id: uuid.UUID) -> Movie | None:
        with trace_span("movie.get_movie_by_id", {"movie_id": str(movie_id)}):
            cached = await self.redis.get_movie(movie_id)
            if cached:
                result = await self.db.execute(
                    select(Movie)
                    .where(Movie.id == movie_id)
                    .options(
                        selectinload(Movie.genres),
                        selectinload(Movie.person_associations)
                        .selectinload(MoviePerson.person),
                    )
                )
                return result.scalar_one_or_none()

            result = await self.db.execute(
                select(Movie)
                .where(Movie.id == movie_id)
                .options(
                    selectinload(Movie.genres),
                    selectinload(Movie.person_associations)
                    .selectinload(MoviePerson.person),
                )
            )
            movie = result.scalar_one_or_none()

            if movie:
                await self.redis.set_movie(
                    movie_id,
                    {
                        "id": str(movie.id),
                        "title": movie.title,
                        "year": movie.year,
                    },
                )

            return movie

    async def create_movie(self, data: MovieCreate) -> Movie:
        with trace_span("movie.create_movie"):
            movie = Movie(
                title=data.title,
                original_title=data.original_title,
                description=data.description,
                year=data.year,
                duration=data.duration,
                poster_url=data.poster_url,
                trailer_url=data.trailer_url,
                rating=data.rating,
                age_rating=data.age_rating,
                imdb_id=data.imdb_id,
                is_published=False,
            )

            self.db.add(movie)
            await self.db.flush()

            if data.genre_ids:
                genres = (await self.db.execute(
                    select(Genre).where(Genre.id.in_(data.genre_ids))
                )).scalars().all()
                movie.genres = list(genres)

            if data.actor_ids:
                actors = (await self.db.execute(
                    select(Person).where(Person.id.in_(data.actor_ids))
                )).scalars().all()
                for actor in actors:
                    self.db.add(MoviePerson(movie=movie, person=actor, role=PersonRole.ACTOR))

            if data.director_ids:
                directors = (await self.db.execute(
                    select(Person).where(Person.id.in_(data.director_ids))
                )).scalars().all()
                for director in directors:
                    self.db.add(MoviePerson(movie=movie, person=director, role=PersonRole.DIRECTOR))

            await self.db.commit()
            await self.db.refresh(movie)

            await self.kafka.publish_movie_created(
                movie.id,
                {"title": movie.title, "year": movie.year, "rating": movie.rating},
            )

            return movie

    async def update_movie(self, movie_id: uuid.UUID, data: MovieUpdate) -> Movie:
        with trace_span("movie.update_movie", {"movie_id": str(movie_id)}):
            movie = await self.get_movie_by_id(movie_id)
            if not movie:
                raise HTTPException(status_code=404, detail="Movie not found")

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(movie, field, value)

            await self.db.commit()
            await self.db.refresh(movie)

            await self.redis.delete_movie(movie_id)

            await self.kafka.publish_movie_updated(
                movie.id,
                {"title": movie.title, "year": movie.year},
            )

            return movie

    async def publish_movie(self, movie_id: uuid.UUID) -> Movie:
        with trace_span("movie.publish_movie", {"movie_id": str(movie_id)}):
            movie = await self.get_movie_by_id(movie_id)
            if not movie:
                raise HTTPException(status_code=404, detail="Movie not found")

            if movie.is_published:
                raise HTTPException(status_code=400, detail="Already published")

            movie.is_published = True
            movie.published_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(movie)

            await self.redis.delete_movie(movie_id)

            await self.kafka.publish_movie_published(
                movie.id,
                {
                    "title": movie.title,
                    "year": movie.year,
                    "published_at": movie.published_at.isoformat(),
                },
            )

            return movie


async def get_movie_service(
    db: AsyncSession = Depends(get_db),
    kafka: KafkaProducerService = Depends(get_kafka_producer),
    redis: RedisService = Depends(get_redis_service),
) -> MovieService:
    return MovieService(db, kafka, redis)
