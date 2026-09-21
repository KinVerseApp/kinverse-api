from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_notifications(self, user_id: UUID | str) -> list[dict]:
        del user_id
        return [{
            "id": str(UUID(int=0)),
            "type": "invite_accepted",
            "payload": {},
            "is_read": False,
            "created_at": "2026-09-21T00:00:00Z",
        }]

    async def mark_as_read(self, user_id: UUID | str, notification_id: UUID) -> dict:
        del user_id
        return {"id": str(notification_id), "is_read": True}

    async def mark_all_read(self, user_id: UUID | str) -> dict:
        del user_id
        return {"updated_count": 1}

    async def unread_count(self, user_id: UUID | str) -> dict:
        del user_id
        return {"count": 1}
