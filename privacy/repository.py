from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import PrivacySetting


class PrivacyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_person(self, person_id: UUID) -> list[PrivacySetting]:
        result = await self.session.execute(
            select(PrivacySetting).where(PrivacySetting.person_id == person_id)
        )
        return list(result.scalars().all())

    async def get(self, person_id: UUID, field_key: str) -> PrivacySetting | None:
        result = await self.session.execute(
            select(PrivacySetting).where(
                PrivacySetting.person_id == person_id, PrivacySetting.field_key == field_key
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, person_id: UUID, field_key: str, visibility: str) -> PrivacySetting:
        existing = await self.get(person_id, field_key)
        if existing is not None:
            existing.visibility = visibility
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        setting = PrivacySetting(person_id=person_id, field_key=field_key, visibility=visibility)
        self.session.add(setting)
        await self.session.commit()
        await self.session.refresh(setting)
        return setting
