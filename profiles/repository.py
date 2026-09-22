from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from users.models import Person


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, person_id: UUID) -> Person | None:
        result = await self.session.execute(select(Person).where(Person.id == person_id))
        return result.scalar_one_or_none()

    async def add(self, person: Person) -> Person:
        self.session.add(person)
        await self.session.commit()
        await self.session.refresh(person)
        return person

    async def update(self, person: Person, changes: dict) -> Person:
        for key, value in changes.items():
            if value is not None and hasattr(person, key):
                setattr(person, key, value)
        await self.session.commit()
        await self.session.refresh(person)
        return person
