from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import ValidationError
from .repository import SearchRepository

MIN_QUERY_LENGTH = 2


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = SearchRepository(session)

    def _validate(self, q: str) -> str:
        q = q.strip()
        if len(q) < MIN_QUERY_LENGTH:
            raise ValidationError(f"Search query must be at least {MIN_QUERY_LENGTH} characters.")
        return q

    async def search_by_name(self, q: str) -> list[dict]:
        q = self._validate(q)
        rows = await self.repository.search_by_name(q)
        return [
            {
                "id": str(r["id"]),
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "match_score": round(float(r["match_score"]), 3),
            }
            for r in rows
        ]

    async def search_by_email(self, q: str) -> list[dict]:
        q = self._validate(q)
        rows = await self.repository.search_by_email(q)
        return [
            {
                "id": str(r["id"]),
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "match_score": r["match_score"],
            }
            for r in rows
        ]

    async def search_existing_members(self, q: str) -> list[dict]:
        # "Search Existing Members" (Discovery Method 2, requirements §3.6)
        # tries name first - that's what the prototype's search screen
        # collects - and falls back to an email match if nothing comes back
        # on name similarity (e.g. the query IS an email address).
        by_name = await self.search_by_name(q)
        if by_name:
            return by_name
        return await self.search_by_email(q)

    async def family_discovery_search(self, q: str) -> list[dict]:
        return await self.search_existing_members(q)
