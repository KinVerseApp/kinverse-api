from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.dependencies import get_current_user
from .schemas import InvitationCreate, InvitationDetail
from .service import InvitationService

router = APIRouter(tags=["invitations"])


@router.post("", response_model=InvitationDetail, summary="Create an invitation")
async def create_invitation(
    payload: InvitationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationDetail:
    service = InvitationService(db)
    result = await service.create_invitation(current_user["sub"], payload.model_dump())
    return InvitationDetail(**result)


@router.post("/email", response_model=InvitationDetail, summary="Send email invite")
async def send_email_invite(
    payload: InvitationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationDetail:
    service = InvitationService(db)
    result = await service.send_email_invite(current_user["sub"], payload.model_dump())
    return InvitationDetail(**result)


@router.post("/sms", response_model=InvitationDetail, summary="Send SMS invite")
async def send_sms_invite(
    payload: InvitationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationDetail:
    service = InvitationService(db)
    result = await service.send_sms_invite(current_user["sub"], payload.model_dump())
    return InvitationDetail(**result)


@router.post("/link", response_model=InvitationDetail, summary="Generate invite link")
async def generate_link(
    payload: InvitationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationDetail:
    service = InvitationService(db)
    result = await service.generate_link(current_user["sub"], payload.model_dump())
    return InvitationDetail(**result)


@router.post("/qr", response_model=InvitationDetail, summary="Generate QR invite")
async def generate_qr(
    payload: InvitationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationDetail:
    service = InvitationService(db)
    result = await service.generate_qr(current_user["sub"], payload.model_dump())
    return InvitationDetail(**result)


@router.post("/{invite_id}/accept", response_model=InvitationDetail, summary="Accept invitation")
async def accept_invitation(
    invite_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationDetail:
    service = InvitationService(db)
    result = await service.accept_invitation(current_user["sub"], invite_id)
    return InvitationDetail(**result)


@router.post("/{invite_id}/decline", response_model=InvitationDetail, summary="Decline invitation")
async def decline_invitation(
    invite_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationDetail:
    service = InvitationService(db)
    result = await service.decline_invitation(current_user["sub"], invite_id)
    return InvitationDetail(**result)
