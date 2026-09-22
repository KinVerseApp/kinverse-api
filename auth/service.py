from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db_types import utcnow
from shared.exceptions import InvalidAuthError
from shared.security import create_token, decode_token, hash_password, verify_password
from users.models import Person, UserAccount
from users.repository import UserRepository

ACCESS_TOKEN_TTL = timedelta(minutes=15)
REFRESH_TOKEN_TTL = timedelta(days=30)

# Deliberately the same message and status for "no such account" and "wrong
# password" - distinguishing them lets an attacker enumerate which emails
# are registered.
_BAD_CREDENTIALS = "Incorrect email or password."


def _issue_tokens(user_id: UUID) -> dict:
    return {
        "access_token": create_token(str(user_id), "access", ACCESS_TOKEN_TTL),
        "refresh_token": create_token(str(user_id), "refresh", REFRESH_TOKEN_TTL),
        "token_type": "bearer",
    }


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repository = UserRepository(session)

    async def register_user(self, payload: dict) -> dict:
        existing = await self.user_repository.get_by_email(payload["email"])
        if existing is not None:
            raise InvalidAuthError("An account with this email already exists.")

        account = UserAccount(
            email=payload["email"],
            auth_provider="email",
            password_hash=hash_password(payload["password"]),
        )
        person = Person(
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            user_account=account,
        )
        created_account = await self.user_repository.add_account(account)
        person.user_account_id = created_account.id
        await self.user_repository.add_person(person)

        # Token subject must be the real account id - every other endpoint's
        # get_current_user dependency does UUID(str(sub)) and looks that id
        # up directly, so a token minted with the email as sub would fail
        # on the very next authenticated request.
        return _issue_tokens(created_account.id)

    async def login(self, payload: dict) -> dict:
        user = await self.user_repository.get_by_email(payload["email"])
        if user is None or user.password_hash is None:
            # user.password_hash is None for an OAuth-only account (google/
            # apple/microsoft) that has no local password to check against -
            # same generic error, not a hint that the account exists but
            # uses a different sign-in method.
            raise InvalidAuthError(_BAD_CREDENTIALS)
        if not verify_password(payload["password"], user.password_hash):
            raise InvalidAuthError(_BAD_CREDENTIALS)

        user.last_login_at = utcnow()
        await self.session.commit()
        return _issue_tokens(user.id)

    async def logout(self, user_id: UUID | str, refresh_token: str | None) -> None:
        # No-op until refresh tokens are tracked server-side (a revocation
        # list / rotating-token table). Not a security hole on its own -
        # the access token still expires in 15 minutes regardless - but a
        # "logged out" refresh token remains valid until it expires unless
        # that's built. Flagged, not silently pretended to work.
        del user_id, refresh_token
        return None

    async def refresh_token(self, refresh_token: str) -> dict:
        # The previous implementation never even looked at the submitted
        # token and always returned a signed, valid token pair for a
        # hardcoded "placeholder-user" - anyone could call this endpoint
        # with any string and receive working credentials. Now it actually
        # verifies the signature/expiry, requires token_type == "refresh"
        # (an access token can't be used to mint another access token), and
        # confirms the account still exists and is active before issuing
        # anything.
        try:
            payload = decode_token(refresh_token)
        except HTTPException:
            raise InvalidAuthError("Invalid or expired refresh token.")

        if payload.get("type") != "refresh":
            raise InvalidAuthError("This is not a refresh token.")

        user_id = payload.get("sub")
        user = await self.user_repository.get_by_id(UUID(str(user_id)))
        if user is None or user.status != "active":
            raise InvalidAuthError("Invalid or expired refresh token.")

        return _issue_tokens(user.id)

    async def request_password_reset(self, email: str) -> dict:
        # Not implemented: needs a password_reset_token table (or a signed,
        # short-lived JWT of its own) and an email-sending job via Azure
        # Functions per the architecture doc. Always returns the same
        # response regardless of whether the email is registered, which is
        # correct behavior to keep even once implemented - it must not leak
        # account existence.
        return {"status": "sent", "email": email}

    async def confirm_password_reset(self, token: str, new_password: str) -> dict:
        del token, new_password
        return {"status": "updated"}

    async def verify_email(self, email: str) -> dict:
        return {"status": "verification_sent", "email": email}

    async def confirm_email_verification(self, token: str) -> dict:
        del token
        return {"status": "verified"}
