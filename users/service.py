from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import NotFoundError
from .repository import UserRepository


class UserService:
    # Registration and logout live in auth/service.py (AuthService) - this
    # module previously had its own separate, unused register_user()/
    # logout() that diverged from the ones actually wired to routes.
    # Two copies of "create a user" is exactly how the auth bug shipped:
    # one implementation got fixed, the other quietly kept working
    # differently. Only what's actually used stays here.

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    async def get_current_user(self, user_id: UUID | str) -> dict:
        account = await self.repository.get_by_id(UUID(str(user_id)))
        if account is None:
            raise NotFoundError("User", str(user_id))
        person = await self.repository.get_person_by_user_id(account.id)
        return {
            "id": str(account.id),
            "email": account.email,
            "first_name": person.first_name if person else "",
            "last_name": person.last_name if person else "",
            "created_at": account.created_at,
        }
