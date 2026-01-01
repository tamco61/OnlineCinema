import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GenreResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


class PersonResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    photo_url: str | None = None

    model_config = {"from_attributes": True}


class MoviePersonResponse(BaseModel):
    person: PersonResponse
    role: str
    character_name: str | None = None

    model_config = {"from_attributes": True}


class MovieBase(BaseModel):
    title: str = Field(..., max_length=500)
    original_title: str | None = Field(None, max_length=500)
    description: str | None = None
    year: int = Field(..., ge=1900, le=2100)
    duration: int | None = Field(None, ge=1, description="Duration in minutes")
    poster_url: str | None = Field(None, max_length=500)
    trailer_url: str | None = Field(None, max_length=500)
    rating: float | None = Field(None, ge=0, le=10)
    age_rating: str | None = Field(None, max_length=10)
    imdb_id: str | None = Field(None, max_length=20)


class MovieCreate(MovieBase):
    genre_ids: list[uuid.UUID] = Field(default_factory=list)
    actor_ids: list[uuid.UUID] = Field(default_factory=list)
    director_ids: list[uuid.UUID] = Field(default_factory=list)


class MovieUpdate(BaseModel):
    title: str | None = None
    original_title: str | None = None
    description: str | None = None
    year: int | None = None
    duration: int | None = None
    poster_url: str | None = None
    trailer_url: str | None = None
    rating: float | None = None
    age_rating: str | None = None
    genre_ids: list[uuid.UUID] | None = None
    actor_ids: list[uuid.UUID] | None = None
    director_ids: list[uuid.UUID] | None = None


class MovieResponse(MovieBase):
    id: uuid.UUID
    is_published: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MovieDetailResponse(MovieResponse):
    genres: list[GenreResponse] = []
    actors: list[PersonResponse] = []
    directors: list[PersonResponse] = []

    model_config = {"from_attributes": True}


class MovieListResponse(BaseModel):
    items: list[MovieResponse]
    total: int
    page: int
    page_size: int
    pages: int
