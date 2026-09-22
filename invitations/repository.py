from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Invitation


class InvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, invitation: Invitation) -> Invitation:
        self.session.add(invitation)
        await self.session.commit()
        await self.session.refresh(invitation)
        return invitation

    async def get_by_id(self, invitation_id: UUID) -> Invitation | None:
        result = await self.session.execute(select(Invitation).where(Invitation.id == invitation_id))
        return result.scalar_one_or_none()

    async def update(self, invitation: Invitation, changes: dict) -> Invitation:
        for key, value in changes.items():
            if value is not None and hasattr(invitation, key):
                setattr(invitation, key, value)
        await self.session.commit()
        await self.session.refresh(invitation)
        return invitation
