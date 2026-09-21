from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import InvalidAuthError, NotFoundError
from shared.security import create_token, hash_password, verify_password
from users.repository import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repository = UserRepository(session)

    async def register_user(self, payload: dict) -> dict:
        user = await self.user_repository.get_by_email(payload["email"])
        if user is not None:
            raise InvalidAuthError("User already exists.")
        password_hash = hash_password(payload["password"])
        return {
            "access_token": create_token(payload["email"], "access", timedelta(minutes=15)),
            "refresh_token": create_token(payload["email"], "refresh", timedelta(days=30)),
            "token_type": "bearer",
            "password_hash": password_hash,
        }

    async def login(self, payload: dict) -> dict:
        user = await self.user_repository.get_by_email(payload["email"])
        if user is None:
            raise NotFoundError("User", payload["email"])
        if not verify_password(payload["password"], user.email):
            raise InvalidAuthError("Incorrect email or password.")
        return {
            "access_token": create_token(str(user.id), "access", timedelta(minutes=15)),
            "refresh_token": create_token(str(user.id), "refresh", timedelta(days=30)),
            "token_type": "bearer",
        }

    async def logout(self, user_id: UUID | str, refresh_token: str | None) -> None:
        del user_id, refresh_token
        return None

    async def refresh_token(self, refresh_token: str) -> dict:
        return {
            "access_token": create_token("placeholder-user", "access", timedelta(minutes=15)),
            "refresh_token": create_token("placeholder-user", "refresh", timedelta(days=30)),
            "token_type": "bearer",
        }

    async def request_password_reset(self, email: str) -> dict:
        return {"status": "sent", "email": email}

    async def confirm_password_reset(self, token: str, new_password: str) -> dict:
        del token, new_password
        return {"status": "updated"}

    async def verify_email(self, email: str) -> dict:
        return {"status": "verification_sent", "email": email}

    async def confirm_email_verification(self, token: str) -> dict:
        del token
        return {"status": "verified"}
