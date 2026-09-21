from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import NotFoundError
from .models import Person, UserAccount
from .repository import UserRepository


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    async def register_user(self, payload: dict) -> dict:
        account = UserAccount(
            email=payload["email"],
            auth_provider=payload.get("auth_provider", "email"),
            auth_provider_subject=payload.get("auth_provider_subject"),
        )
        person = Person(
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            user_account=account,
        )
        created_account = await self.repository.add_account(account)
        person.user_account_id = created_account.id
        await self.repository.add_person(person)
        return {"id": str(created_account.id), "email": created_account.email}

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

    async def logout(self, user_id: UUID | str, refresh_token: str | None) -> None:
        del user_id, refresh_token
        return None
