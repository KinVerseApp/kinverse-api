from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base
from shared.db_types import UTCDateTime, utcnow
from shared.pg_enums import AccountStatusEnum, AuthProviderEnum, DobPrecisionEnum, GenderEnum, VisibilityEnum


class UserAccount(Base):
    __tablename__ = "user_account"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    auth_provider: Mapped[str] = mapped_column(AuthProviderEnum, nullable=False)
    auth_provider_subject: Mapped[str | None] = mapped_column(String, nullable=True)
    # Only set for auth_provider == "email". NULL for google/apple/microsoft
    # accounts, which authenticate via auth_provider_subject instead.
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    status: Mapped[str] = mapped_column(AccountStatusEnum, default="active", nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False, onupdate=utcnow)

    # Person has two FKs to user_account (user_account_id, created_by_user_account_id) —
    # foreign_keys must be explicit or SQLAlchemy can't tell which one this relates on.
    person: Mapped["Person | None"] = relationship(
        back_populates="user_account", foreign_keys="Person.user_account_id"
    )


class Person(Base):
    __tablename__ = "person"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("user_account.id"), nullable=True, unique=True)
    created_by_user_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("user_account.id"), nullable=True)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    dob_precision: Mapped[str] = mapped_column(DobPrecisionEnum, default="unknown", nullable=False)
    gender: Mapped[str | None] = mapped_column(GenderEnum, nullable=True)
    profile_photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    native_country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    native_state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    native_district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    native_village: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_deceased: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deceased_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    default_visibility: Mapped[str] = mapped_column(VisibilityEnum, default="family_network", nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False, onupdate=utcnow)

    user_account: Mapped["UserAccount | None"] = relationship(
        back_populates="person", foreign_keys=[user_account_id]
    )
