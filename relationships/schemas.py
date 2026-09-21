from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RelationshipCreate(BaseModel):
    person_a_id: UUID
    person_b_id: UUID
    edge_type: Literal["parent_child", "partner"] = "parent_child"
    partner_type: str | None = None
    source: str = "manual"
    start_date: date | None = None


class RelationshipUpdate(BaseModel):
    status: str | None = None
    source: str | None = None
    partner_type: str | None = None
    start_date: date | None = None


class RelationshipDetail(BaseModel):
    id: UUID
    person_a_id: UUID
    person_b_id: UUID
    edge_type: str
    status: str = "pending"
    source: str = "manual"
    partner_type: str | None = None
