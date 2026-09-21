from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class UserAccount(Base):
    __tablename__ = "user_account"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    auth_provider: Mapped[str] = mapped_column(String(20), nullable=False)
    auth_provider_subject: Mapped[str | None] = mapped_column(String, nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)

    person: Mapped["Person | None"] = relationship(back_populates="user_account")


class Person(Base):
    __tablename__ = "person"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("user_account.id"), nullable=True, unique=True)
    created_by_user_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("user_account.id"), nullable=True)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    dob_precision: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
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
    default_visibility: Mapped[str] = mapped_column(String(30), default="family_network", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)

    user_account: Mapped["UserAccount | None"] = relationship(back_populates="person")
