from typing import Optional

from pydantic import BaseModel, Field


# todo: uuid


class ViewingEventCreate(BaseModel):
    user_id: str = Field(..., description="User UUID")
    movie_id: str = Field(..., description="Movie UUID")
    event_type: str = Field(..., description="Event type: start, progress, finish")
    position_seconds: int = Field(0, ge=0, description="Playback position in seconds")
    session_id: Optional[str] = Field(None, description="Session UUID")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class PopularContentItem(BaseModel):
    movie_id: str
    total_views: int
    unique_viewers: int
    completion_rate: Optional[float] = None

    class Config:
        from_attributes = True


class PopularContentResponse(BaseModel):
    items: list[PopularContentItem]
    period_days: int
    total_items: int


class UserStatsResponse(BaseModel):
    user_id: str
    movies_started: int
    movies_finished: int
    unique_movies_watched: int
    total_watch_time_seconds: int
    completion_rate: float
    period_days: int
    most_watched_movie_id: Optional[str] = None

    class Config:
        from_attributes = True
