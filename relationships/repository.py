from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import RelationshipEdge


class RelationshipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_edge(self, edge: RelationshipEdge) -> RelationshipEdge:
        self.session.add(edge)
        await self.session.commit()
        await self.session.refresh(edge)
        return edge

    async def get_by_id(self, relationship_id: UUID) -> RelationshipEdge | None:
        result = await self.session.execute(
            select(RelationshipEdge).where(RelationshipEdge.id == relationship_id)
        )
        return result.scalar_one_or_none()

    async def update(self, edge: RelationshipEdge, changes: dict) -> RelationshipEdge:
        for key, value in changes.items():
            if value is not None and hasattr(edge, key):
                setattr(edge, key, value)
        await self.session.commit()
        await self.session.refresh(edge)
        return edge

    async def delete(self, edge: RelationshipEdge) -> None:
        await self.session.delete(edge)
        await self.session.commit()
