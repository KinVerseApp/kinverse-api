from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class TreeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_tree(self, user_id: UUID | str, root_id: UUID | None = None, limit: int = 50) -> dict:
        del user_id
        return {"root_id": str(root_id) if root_id else None, "nodes": [], "total_visible": 0, "limit": limit}

    async def get_ancestors(self, person_id: UUID) -> list[dict]:
        return [{"id": str(person_id), "relationship": "ancestor"}]

    async def get_descendants(self, person_id: UUID) -> list[dict]:
        return [{"id": str(person_id), "relationship": "descendant"}]

    async def get_siblings(self, person_id: UUID) -> list[dict]:
        return [{"id": str(person_id), "relationship": "sibling"}]

    async def get_cousins(self, person_id: UUID) -> list[dict]:
        return [{"id": str(person_id), "relationship": "cousin"}]

    async def get_aunts_and_uncles(self, person_id: UUID) -> list[dict]:
        return [{"id": str(person_id), "relationship": "aunt_or_uncle"}]

    async def get_in_laws(self, person_id: UUID) -> list[dict]:
        return [{"id": str(person_id), "relationship": "in_law"}]

    async def get_family_completeness_score(self, user_id: UUID | str, person_id: UUID) -> dict:
        del user_id, person_id
        return {"score": 0.0, "coverage": "not_available"}
