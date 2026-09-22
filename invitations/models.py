from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base
from shared.db_types import UTCDateTime, utcnow
from shared.pg_enums import InvitationMethodEnum, InvitationScopeEnum, InvitationStatusEnum


def _default_expiry() -> datetime:
    return utcnow() + timedelta(days=14)


class Invitation(Base):
    __tablename__ = "invitation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inviter_user_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_account.id"), nullable=False
    )
    # Null only for an open tree-join link/QR not yet tied to a specific person
    invitee_person_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("person.id", ondelete="CASCADE"), nullable=True
    )
    scope: Mapped[str] = mapped_column(InvitationScopeEnum, default="person", nullable=False)
    method: Mapped[str] = mapped_column(InvitationMethodEnum, nullable=False)
    channel_value: Mapped[str | None] = mapped_column(String, nullable=True)
    invite_code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(InvitationStatusEnum, default="pending", nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=_default_expiry)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
