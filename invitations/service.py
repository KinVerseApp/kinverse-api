from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class InvitationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_invitation(self, user_id: UUID, payload: dict) -> dict:
        del user_id
        return {"id": str(UUID(int=0)), "invite_code": "KIN-123456", **payload, "status": "pending"}

    async def send_email_invite(self, user_id: UUID, payload: dict) -> dict:
        return await self.create_invitation(user_id, payload)

    async def send_sms_invite(self, user_id: UUID, payload: dict) -> dict:
        return await self.create_invitation(user_id, payload)

    async def generate_link(self, user_id: UUID, payload: dict) -> dict:
        return await self.create_invitation(user_id, payload)

    async def generate_qr(self, user_id: UUID, payload: dict) -> dict:
        return await self.create_invitation(user_id, payload)

    async def accept_invitation(self, user_id: UUID, invite_id: UUID) -> dict:
        del user_id
        return {"id": str(invite_id), "status": "accepted"}

    async def decline_invitation(self, user_id: UUID, invite_id: UUID) -> dict:
        del user_id
        return {"id": str(invite_id), "status": "declined"}
