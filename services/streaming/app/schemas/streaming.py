from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class StreamRequest(BaseModel):
    manifest_type: str = Field("hls", description="Manifest type: hls or dash")


class StreamResponse(BaseModel):
    manifest_url: str = Field(..., description="Signed URL for manifest file")
    expires_in: int = Field(..., description="URL expiration in seconds")
    manifest_type: str = Field(..., description="Manifest type (hls/dash)")


class ProgressUpdateRequest(BaseModel):
    position_seconds: int = Field(..., ge=0, description="Current playback position in seconds")


class ProgressUpdateResponse(BaseModel):
    success: bool
    position_seconds: int
    message: str = "Progress updated successfully"


class WatchProgressResponse(BaseModel):
    user_id: str
    movie_id: str
    position_seconds: int
    last_watched_at: Optional[datetime] = None

    class Config:
        from_attributes = True
