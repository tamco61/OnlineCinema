from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class WatchHistoryBase(BaseModel):
    content_id: UUID
    content_type: str = Field(..., max_length=20)
    progress_seconds: int = Field(default=0, ge=0)
    duration_seconds: int | None = Field(None, ge=0)


class WatchHistoryCreate(WatchHistoryBase):
    pass


class WatchHistoryUpdate(BaseModel):
    content_id: UUID
    content_type: str
    progress_seconds: int = Field(..., ge=0)
    duration_seconds: int | None = Field(None, ge=0)
    completed: bool = False


class WatchHistoryResponse(WatchHistoryBase):
    id: UUID
    profile_id: UUID
    completed: bool
    last_watched_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
