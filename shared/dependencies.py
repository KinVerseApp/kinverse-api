from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .exceptions import InvalidAuthError
from .security import decode_token

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if credentials is None:
        raise InvalidAuthError("Missing bearer token.")

    payload = decode_token(credentials.credentials)

    # Only access tokens authorize API calls. A refresh token is long-lived
    # (30 days) and must only ever be exchanged at /auth/refresh - accepting
    # it here would make the 15-minute access-token expiry meaningless.
    if payload.get("type") != "access":
        raise InvalidAuthError("An access token is required.")

    # Every service does UUID(str(sub)); a signed token whose subject isn't a
    # UUID would otherwise crash there with a 500 instead of being rejected.
    user_id = payload.get("sub")
    try:
        UUID(str(user_id))
    except ValueError:
        raise InvalidAuthError("Token subject is invalid.") from None

    return {"sub": user_id, "token_type": payload.get("type"), "db": db}
