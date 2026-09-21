from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_existing_members(self, q: str) -> list[dict]:
        return [{"id": "1", "first_name": "Sample", "last_name": "Match", "match_score": 0.9}] if q else []

    async def search_by_name(self, q: str) -> list[dict]:
        return await self.search_existing_members(q)

    async def search_by_email(self, q: str) -> list[dict]:
        return [{"id": "2", "first_name": "Email", "last_name": "User", "match_score": 1.0}] if q else []

    async def family_discovery_search(self, q: str) -> list[dict]:
        return await self.search_existing_members(q)
