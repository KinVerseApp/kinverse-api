from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InvitationCreate(BaseModel):
    invitee_email: str | None = None
    person_id: UUID | None = None
    method: str = "email"
    scope: str = "person"


class InvitationDetail(BaseModel):
    id: UUID
    invite_code: str
    method: str
    status: str = "pending"
    expires_at: datetime | None = None
