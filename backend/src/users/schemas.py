import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)

from src.users.models import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )
    first_name: str = Field(
        min_length=2,
        max_length=50,
    )
    last_name: str = Field(
        min_length=2,
        max_length=50,
    )
    phone: str | None = Field(
        default=None,
        max_length=30,
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128,
    )


class UserProfileUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )
    last_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )
    phone: str | None = Field(
        default=None,
        max_length=30,
    )


class UserAvatarResponse(BaseModel):
    avatar_url: str


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"