from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class FavoriteBase(BaseModel):
    content_id: UUID
    content_type: str = Field(..., max_length=20)


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteResponse(FavoriteBase):
    id: UUID
    profile_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
