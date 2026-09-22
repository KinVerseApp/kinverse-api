from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base
from shared.db_types import UTCDateTime, utcnow
from shared.pg_enums import PrivacyFieldEnum, VisibilityEnum


class PrivacySetting(Base):
    __tablename__ = "privacy_setting"
    __table_args__ = (UniqueConstraint("person_id", "field_key", name="uq_privacy_person_field"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("person.id", ondelete="CASCADE"), nullable=False
    )
    field_key: Mapped[str] = mapped_column(PrivacyFieldEnum, nullable=False)
    visibility: Mapped[str] = mapped_column(VisibilityEnum, default="family_network", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
