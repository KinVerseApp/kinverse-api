from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.dependencies import get_current_user
from .schemas import CurrentUserResponse, UserDetail
from .service import UserService

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserDetail, summary="Get current user")
async def get_current_user_route(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserDetail:
    service = UserService(db)
    result = await service.get_current_user(current_user["sub"])
    return UserDetail(**result)
