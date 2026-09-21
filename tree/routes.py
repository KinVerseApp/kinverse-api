from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.dependencies import get_current_user
from .schemas import FamilyCompletenessScore, TreeResponse
from .service import TreeService

router = APIRouter(tags=["tree"])


@router.get("", response_model=TreeResponse, summary="Get the family tree")
async def get_tree(
    root_id: UUID | None = None,
    branch_limit: int = Query(default=50, le=50),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TreeResponse:
    service = TreeService(db)
    result = await service.get_tree(current_user["sub"], root_id=root_id, limit=branch_limit)
    return TreeResponse(**result)


@router.get("/ancestors", summary="Get ancestors")
async def get_ancestors(
    person_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    service = TreeService(db)
    return await service.get_ancestors(person_id)


@router.get("/descendants", summary="Get descendants")
async def get_descendants(
    person_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    service = TreeService(db)
    return await service.get_descendants(person_id)


@router.get("/{person_id}/siblings", summary="Get siblings")
async def get_siblings(
    person_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    service = TreeService(db)
    return await service.get_siblings(person_id)


@router.get("/completeness", response_model=FamilyCompletenessScore, summary="Get family completeness score")
async def get_family_completeness_score(
    person_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FamilyCompletenessScore:
    service = TreeService(db)
    result = await service.get_family_completeness_score(current_user["sub"], person_id)
    return FamilyCompletenessScore(**result)
