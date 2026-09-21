from __future__ import annotations

from pydantic import BaseModel


class PrivacySetting(BaseModel):
    field_key: str
    visibility: str = "family_network"


class PrivacySettingsResponse(BaseModel):
    settings: list[PrivacySetting] = []
