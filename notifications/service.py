from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import NotFoundError, PermissionDeniedError
from .models import Notification
from .repository import NotificationRepository


def _detail(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "type": notification.type,
        "payload": notification.payload,
        "is_read": notification.is_read,
        "created_at": notification.created_at,
    }


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = NotificationRepository(session)

    async def list_notifications(self, user_id: UUID | str) -> list[dict]:
        rows = await self.repository.list_for_user(UUID(str(user_id)))
        return [_detail(n) for n in rows]

    async def mark_as_read(self, user_id: UUID | str, notification_id: UUID) -> dict:
        notification = await self.repository.get_by_id(notification_id)
        if notification is None:
            raise NotFoundError("Notification", str(notification_id))
        if str(notification.recipient_user_account_id) != str(user_id):
            raise PermissionDeniedError("This notification does not belong to you.")
        updated = await self.repository.mark_read(notification)
        return _detail(updated)

    async def mark_all_read(self, user_id: UUID | str) -> dict:
        updated_count = await self.repository.mark_all_read(UUID(str(user_id)))
        return {"updated_count": updated_count}

    async def unread_count(self, user_id: UUID | str) -> dict:
        count = await self.repository.unread_count(UUID(str(user_id)))
        return {"count": count}
