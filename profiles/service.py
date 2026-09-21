from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_profile(self, user_id: UUID, payload: dict) -> dict:
        del user_id
        return {"id": str(UUID(int=0)), **payload}

    async def update_profile(self, user_id: UUID, person_id: UUID, payload: dict) -> dict:
        del user_id, person_id
        return {"id": str(person_id), **payload}

    async def get_profile(self, user_id: UUID, person_id: UUID) -> dict:
        del user_id
        return {"id": str(person_id), "first_name": "Sample", "last_name": "Profile"}

    async def upload_profile_image(self, user_id: UUID, person_id: UUID, file_name: str) -> dict:
        del user_id, person_id
        return {"profile_photo_url": file_name}

    async def get_heritage(self, user_id: UUID, person_id: UUID) -> dict:
        del user_id, person_id
        return {"native_country": "Kenya", "native_state": "Nairobi"}

    async def update_heritage(self, user_id: UUID, person_id: UUID, payload: dict) -> dict:
        del user_id, person_id
        return {"status": "updated", **payload}
