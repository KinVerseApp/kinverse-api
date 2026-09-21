from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    date_of_birth: date | None = None
    gender: str | None = None
    biography: str | None = None
    default_visibility: str = "family_network"


class ProfileUpdate(ProfileCreate):
    pass


class ProfileDetail(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    gender: str | None = None
    biography: str | None = None
    profile_photo_url: str | None = None
    default_visibility: str = "family_network"


class HeritageInfo(BaseModel):
    native_country: str | None = None
    native_state: str | None = None
    native_district: str | None = None
    native_village: str | None = None


class ProfileImageResponse(BaseModel):
    profile_photo_url: str
