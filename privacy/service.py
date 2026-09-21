from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class PrivacyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_privacy_settings(self, user_id: UUID | str, person_id: UUID | None = None) -> list[dict]:
        del user_id, person_id
        return [{"field_key": "email", "visibility": "family_network"}]

    async def update_privacy_settings(self, user_id: UUID | str, payload: dict) -> list[dict]:
        del user_id
        return list(payload.get("settings", []))

    async def get_visibility_filter(self, user_id: UUID | str) -> dict:
        del user_id
        return {"visibility": "family_network"}
