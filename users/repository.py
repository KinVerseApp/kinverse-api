from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Person, UserAccount


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> UserAccount | None:
        result = await self.session.execute(select(UserAccount).where(UserAccount.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> UserAccount | None:
        result = await self.session.execute(select(UserAccount).where(UserAccount.id == user_id))
        return result.scalar_one_or_none()

    async def get_person_by_user_id(self, user_id: UUID) -> Person | None:
        result = await self.session.execute(select(Person).where(Person.user_account_id == user_id))
        return result.scalar_one_or_none()

    async def add_account(self, record: UserAccount) -> UserAccount:
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def add_person(self, record: Person) -> Person:
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record
