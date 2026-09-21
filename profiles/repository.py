from __future__ import annotations

from uuid import UUID


class ProfileRepository:
    async def get_profile(self, person_id: UUID) -> dict | None:
        return {"id": str(person_id)}

    async def save_profile(self, person_id: UUID, payload: dict) -> dict:
        return {"id": str(person_id), **payload}
