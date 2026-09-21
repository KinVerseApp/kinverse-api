from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.dependencies import get_current_user
from .schemas import RelationshipCreate, RelationshipDetail, RelationshipUpdate
from .service import RelationshipService

router = APIRouter(tags=["relationships"])


@router.post("", response_model=RelationshipDetail, summary="Add a relationship")
async def add_relative(
    payload: RelationshipCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelationshipDetail:
    service = RelationshipService(db)
    result = await service.add_relative(current_user["sub"], payload.model_dump())
    return RelationshipDetail(**result)


@router.patch("/{relationship_id}", response_model=RelationshipDetail, summary="Update a relationship")
async def update_relationship(
    relationship_id: UUID,
    payload: RelationshipUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelationshipDetail:
    service = RelationshipService(db)
    result = await service.update_relationship(current_user["sub"], relationship_id, payload.model_dump())
    return RelationshipDetail(**result)


@router.post("/{relationship_id}/confirm", response_model=RelationshipDetail, summary="Confirm a relationship")
async def confirm_relationship(
    relationship_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelationshipDetail:
    service = RelationshipService(db)
    result = await service.confirm_relationship(current_user["sub"], relationship_id)
    return RelationshipDetail(**result)


@router.post("/{relationship_id}/reject", summary="Reject a relationship")
async def reject_relationship(
    relationship_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = RelationshipService(db)
    return await service.reject_relationship(current_user["sub"], relationship_id)


@router.delete("/{relationship_id}", status_code=204, summary="Remove relationship")
async def remove_relationship(
    relationship_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = RelationshipService(db)
    await service.remove_relationship(current_user["sub"], relationship_id)
