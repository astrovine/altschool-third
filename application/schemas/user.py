from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from application.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole
    is_active: bool
    is_banned: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserBanUpdate(BaseModel):
    is_banned: bool
