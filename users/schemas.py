from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)


class UserSummary(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    created_at: datetime


class UserDetail(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    phone_number: str | None = None
    profile_photo_url: str | None = None
    default_visibility: str = "family_network"
    created_at: datetime


class CurrentUserResponse(BaseModel):
    user: UserDetail
