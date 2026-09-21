from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.dependencies import get_current_user
from .schemas import PrivacySetting, PrivacySettingsResponse
from .service import PrivacyService

router = APIRouter(tags=["privacy"])


@router.get("", response_model=PrivacySettingsResponse, summary="Get privacy settings")
async def get_privacy_settings(
    person_id: UUID | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PrivacySettingsResponse:
    service = PrivacyService(db)
    result = await service.get_privacy_settings(current_user["sub"], person_id)
    return PrivacySettingsResponse(settings=[PrivacySetting(**item) for item in result])


@router.patch("", response_model=PrivacySettingsResponse, summary="Update privacy settings")
async def update_privacy_settings(
    payload: PrivacySettingsResponse,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PrivacySettingsResponse:
    service = PrivacyService(db)
    result = await service.update_privacy_settings(current_user["sub"], payload.model_dump())
    return PrivacySettingsResponse(settings=[PrivacySetting(**item) for item in result])


@router.get("/visibility", summary="Get visibility filtering")
async def get_visibility_filter(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = PrivacyService(db)
    return await service.get_visibility_filter(current_user["sub"])
