from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class TreeNode(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    relationship: str | None = None
    children: list["TreeNode"] = []


class TreeResponse(BaseModel):
    root_id: UUID | None = None
    nodes: list[TreeNode] = []
    total_visible: int = 0


class FamilyCompletenessScore(BaseModel):
    score: float
    coverage: str
