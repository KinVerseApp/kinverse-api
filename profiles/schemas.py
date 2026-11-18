from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# Mirror gender_enum / visibility_enum (shared/pg_enums.py) so an invalid
# value is a 422 here instead of a Postgres enum error (500) on INSERT.
Gender = Literal["female", "male", "non_binary", "unspecified"]
Visibility = Literal["public", "family_network", "direct_relatives", "private"]


class ProfileCreate(BaseModel):
    # max_length matches person.first_name/last_name VARCHAR(120).
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    date_of_birth: date | None = None
    gender: Gender | None = None
    biography: str | None = None
    default_visibility: Visibility = "family_network"


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
    # VARCHAR(120) columns on person.
    native_country: str | None = Field(default=None, max_length=120)
    native_state: str | None = Field(default=None, max_length=120)
    native_district: str | None = Field(default=None, max_length=120)
    native_village: str | None = Field(default=None, max_length=120)


class ProfileImageResponse(BaseModel):
    profile_photo_url: str
