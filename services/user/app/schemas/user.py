from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserProfileBase(BaseModel):
    nickname: Optional[str] = Field(None, max_length=100, description="User nickname")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL")
    language: str = Field(default="en", max_length=10, description="ISO 639-1 language code")
    country: Optional[str] = Field(None, max_length=2, description="ISO 3166-1 alpha-2 country code")


class UserProfileCreate(UserProfileBase):
    user_id: UUID = Field(..., description="User ID from auth-service")


class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    language: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=2)


class UserProfileResponse(UserProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
