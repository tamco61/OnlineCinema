import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

    # todo переделать validate_password
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return v


class UserLogin(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)


class UserResponse(BaseModel):
    id: uuid.UUID = Field(...)
    email: EmailStr = Field(...)
    is_active: bool = Field(...)
    created_at: datetime = Field(...)

    model_config = {"from_attributes": True}


class TokenPair(BaseModel):
    access_token: str = Field(...)
    refresh_token: str = Field(...)
    token_type: str = Field(...)
    expires_in: int = Field(...)


class TokenRefresh(BaseModel):
    refresh_token: str = Field(...)


class TokenResponse(BaseModel):
    access_token: str = Field(...)
    token_type: str = Field(...)
    expires_in: int = Field(...)


class AuthResponse(BaseModel):
    user: UserResponse = Field(...)
    tokens: TokenPair = Field(...)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(...)


class MessageResponse(BaseModel):
    message: str = Field(...)
