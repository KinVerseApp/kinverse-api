from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.dependencies import get_current_user
from .schemas import SearchResult
from .service import SearchService

router = APIRouter(tags=["search"])


@router.get("", response_model=list[SearchResult], summary="Search existing members")
async def search_existing_members(
    q: str = Query(..., alias="q"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SearchResult]:
    del current_user
    service = SearchService(db)
    result = await service.search_existing_members(q)
    return [SearchResult(**item) for item in result]


@router.get("/name", response_model=list[SearchResult], summary="Search by name")
async def search_by_name(
    q: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SearchResult]:
    del current_user
    service = SearchService(db)
    result = await service.search_by_name(q)
    return [SearchResult(**item) for item in result]


@router.get("/email", response_model=list[SearchResult], summary="Search by email")
async def search_by_email(
    q: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SearchResult]:
    del current_user
    service = SearchService(db)
    result = await service.search_by_email(q)
    return [SearchResult(**item) for item in result]


@router.get("/discovery", response_model=list[SearchResult], summary="Family discovery search")
async def family_discovery_search(
    q: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SearchResult]:
    del current_user
    service = SearchService(db)
    result = await service.family_discovery_search(q)
    return [SearchResult(**item) for item in result]
