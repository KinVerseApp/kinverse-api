from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.dependencies import get_current_user
from .schemas import HeritageInfo, ProfileCreate, ProfileDetail, ProfileImageResponse, ProfileUpdate
from .service import ProfileService

router = APIRouter(tags=["profiles"])


@router.post("", response_model=ProfileDetail, summary="Create a person profile")
async def create_profile(
    payload: ProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileDetail:
    service = ProfileService(db)
    result = await service.create_profile(current_user["sub"], payload.model_dump())
    return ProfileDetail(**result)


@router.get("/{person_id}", response_model=ProfileDetail, summary="Get a profile")
async def get_profile(
    person_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileDetail:
    service = ProfileService(db)
    result = await service.get_profile(current_user["sub"], person_id)
    return ProfileDetail(**result)


@router.patch("/{person_id}", response_model=ProfileDetail, summary="Update profile")
async def update_profile(
    person_id: UUID,
    payload: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileDetail:
    service = ProfileService(db)
    result = await service.update_profile(current_user["sub"], person_id, payload.model_dump())
    return ProfileDetail(**result)


@router.post("/{person_id}/image", response_model=ProfileImageResponse, summary="Upload profile image")
async def upload_profile_image(
    person_id: UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileImageResponse:
    service = ProfileService(db)
    result = await service.upload_profile_image(current_user["sub"], person_id, file.filename or "profile-image")
    return ProfileImageResponse(**result)


@router.get("/{person_id}/heritage", response_model=HeritageInfo, summary="Get heritage information")
async def get_heritage(
    person_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HeritageInfo:
    service = ProfileService(db)
    result = await service.get_heritage(current_user["sub"], person_id)
    return HeritageInfo(**result)


@router.patch("/{person_id}/heritage", response_model=HeritageInfo, summary="Update heritage information")
async def update_heritage(
    person_id: UUID,
    payload: HeritageInfo,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HeritageInfo:
    service = ProfileService(db)
    result = await service.update_heritage(current_user["sub"], person_id, payload.model_dump())
    return HeritageInfo(**result)
