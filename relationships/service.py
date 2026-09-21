from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class RelationshipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_relative(self, user_id: UUID, payload: dict) -> dict:
        del user_id
        return {"id": str(UUID(int=0)), **payload, "status": "pending"}

    async def update_relationship(self, user_id: UUID, relationship_id: UUID, payload: dict) -> dict:
        del user_id
        return {"id": str(relationship_id), **payload}

    async def confirm_relationship(self, user_id: UUID, relationship_id: UUID) -> dict:
        del user_id
        return {"id": str(relationship_id), "status": "confirmed"}

    async def reject_relationship(self, user_id: UUID, relationship_id: UUID) -> dict:
        del user_id
        return {"id": str(relationship_id), "status": "rejected"}

    async def remove_relationship(self, user_id: UUID, relationship_id: UUID) -> None:
        del user_id, relationship_id
        return None
