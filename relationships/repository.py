from __future__ import annotations

from uuid import UUID


class RelationshipRepository:
    async def add_edge(self, payload: dict) -> dict:
        return {"id": str(UUID(int=0)), **payload}

    async def get_related(self, person_id: UUID) -> list[dict]:
        return [{"person_id": str(person_id), "relationship": "self"}]
