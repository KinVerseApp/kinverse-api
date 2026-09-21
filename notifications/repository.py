from __future__ import annotations

from uuid import UUID


class NotificationRepository:
    async def list(self, user_id: UUID | str) -> list[dict]:
        del user_id
        return []
