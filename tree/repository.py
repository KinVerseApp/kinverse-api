from __future__ import annotations

from uuid import UUID


class TreeRepository:
    async def get_tree(self, root_id: UUID | None, limit: int = 50) -> list[dict]:
        del root_id
        return []

    async def get_ancestors(self, person_id: UUID) -> list[dict]:
        return [{"id": str(person_id), "relationship": "ancestor"}]

    async def get_descendants(self, person_id: UUID) -> list[dict]:
        return [{"id": str(person_id), "relationship": "descendant"}]
