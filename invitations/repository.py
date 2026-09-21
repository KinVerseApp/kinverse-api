from __future__ import annotations

from uuid import UUID


class InvitationRepository:
    async def save(self, payload: dict) -> dict:
        return {"id": str(UUID(int=0)), **payload}
