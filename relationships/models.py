from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base
from shared.db_types import UTCDateTime, utcnow
from shared.pg_enums import EdgeSourceEnum, EdgeStatusEnum, EdgeTypeEnum, PartnerTypeEnum


class RelationshipEdge(Base):
    """Mirrors relationship_edge in kinverse_schema.sql (kinverse-project repo).

    Only two edge_type values are ever stored:
      - 'parent_child' : directed, person_a_id is the parent of person_b_id
      - 'partner'       : symmetric, stored once with person_a_id < person_b_id

    Every named relationship the app shows (sibling, grandparent, aunt/uncle,
    cousin, in-law, ...) is DERIVED from these two edge types at query time —
    see tree/repository.py. Nothing else is ever stored here.
    """

    __tablename__ = "relationship_edge"
    __table_args__ = (
        UniqueConstraint("person_a_id", "person_b_id", "edge_type", name="uq_edge_pair_type"),
        CheckConstraint("person_a_id <> person_b_id", name="chk_edge_not_self"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_a_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("person.id", ondelete="CASCADE"), nullable=False
    )
    person_b_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("person.id", ondelete="CASCADE"), nullable=False
    )
    edge_type: Mapped[str] = mapped_column(EdgeTypeEnum, nullable=False)
    partner_type: Mapped[str | None] = mapped_column(PartnerTypeEnum, nullable=True)
    status: Mapped[str] = mapped_column(EdgeStatusEnum, default="pending", nullable=False)
    source: Mapped[str] = mapped_column(EdgeSourceEnum, default="manual", nullable=False)
    created_by_user_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user_account.id"), nullable=True
    )
    confirmed_by_person_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("person.id"), nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, nullable=False, onupdate=utcnow
    )
