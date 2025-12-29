from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# todo: rework UUID

class GenreInfo(BaseModel):
    id: str
    name: str
    slug: str


class PersonInfo(BaseModel):
    id: str
    full_name: str
    character_name: Optional[str] = None


class DirectorInfo(BaseModel):
    id: str
    full_name: str


class MovieSearchResult(BaseModel):
    movie_id: str
    title: str
    original_title: Optional[str] = None
    description: Optional[str] = None
    year: int
    duration: Optional[int] = None
    rating: Optional[float] = None
    age_rating: Optional[str] = None
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    genres: list[GenreInfo] = []
    actors: list[PersonInfo] = []
    directors: list[DirectorInfo] = []
    is_published: bool = False
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query (title, description, actors, directors)")
    genres: Optional[list[str]] = Field(None, description="Filter by genre slugs")
    year_from: Optional[int] = Field(None, ge=1900, le=2100, description="Minimum year")
    year_to: Optional[int] = Field(None, ge=1900, le=2100, description="Maximum year")
    rating_from: Optional[float] = Field(None, ge=0.0, le=10.0, description="Minimum rating")
    rating_to: Optional[float] = Field(None, ge=0.0, le=10.0, description="Maximum rating")
    age_rating: Optional[list[str]] = Field(None, description="Filter by age rating (G, PG, PG-13, R, NC-17)")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    published_only: bool = Field(True, description="Show only published movies")


class SearchResponse(BaseModel):
    results: list[MovieSearchResult]
    total: int
    page: int
    size: int
    total_pages: int


class SuggestionItem(BaseModel):
    movie_id: str
    title: str
    year: int
    poster_url: Optional[str] = None


class SuggestRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Autocomplete query (minimum 2 characters)")
    limit: int = Field(10, ge=1, le=20, description="Maximum number of suggestions")


class SuggestResponse(BaseModel):
    suggestions: list[SuggestionItem]
