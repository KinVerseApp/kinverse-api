from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.dependencies import get_current_user
from .schemas import NotificationSummary
from .service import NotificationService

router = APIRouter(tags=["notifications"])


@router.get("", response_model=list[NotificationSummary], summary="List notifications")
async def list_notifications(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationSummary]:
    service = NotificationService(db)
    result = await service.list_notifications(current_user["sub"])
    return [NotificationSummary(**item) for item in result]


@router.patch("/{notification_id}/read", response_model=NotificationSummary, summary="Mark notification as read")
async def mark_as_read(
    notification_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationSummary:
    service = NotificationService(db)
    result = await service.mark_as_read(current_user["sub"], notification_id)
    return NotificationSummary(**result)


@router.patch("/read-all", summary="Mark all notifications as read")
async def mark_all_read(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = NotificationService(db)
    return await service.mark_all_read(current_user["sub"])


@router.get("/unread-count", summary="Get unread notification count")
async def unread_count(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = NotificationService(db)
    return await service.unread_count(current_user["sub"])
