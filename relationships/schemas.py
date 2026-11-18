from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

# Mirror the Postgres enums in shared/pg_enums.py. Typing these as Literal
# rejects a bad value with a 422 at the request boundary - as plain str, it
# reached the INSERT and Postgres rejected it there, surfacing as a 500.
EdgeType = Literal["parent_child", "partner"]
PartnerType = Literal["spouse", "partner", "ex_spouse", "ex_partner"]
EdgeStatus = Literal["pending", "confirmed", "rejected"]
EdgeSource = Literal["manual", "invite_accept", "search_match", "ai_suggested"]


class RelationshipCreate(BaseModel):
    person_a_id: UUID
    person_b_id: UUID
    edge_type: EdgeType = "parent_child"
    partner_type: PartnerType | None = None
    source: EdgeSource = "manual"
    start_date: date | None = None


class RelationshipUpdate(BaseModel):
    status: EdgeStatus | None = None
    source: EdgeSource | None = None
    partner_type: PartnerType | None = None
    start_date: date | None = None


class RelationshipDetail(BaseModel):
    id: UUID
    person_a_id: UUID
    person_b_id: UUID
    edge_type: str
    status: str = "pending"
    source: str = "manual"
    partner_type: str | None = None
