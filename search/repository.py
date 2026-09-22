from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_by_name(self, query: str, limit: int = 20) -> list[dict]:
        # Uses the pg_trgm GIN index (idx_person_name_trgm) already defined in
        # kinverse_schema.sql - trigram similarity via the % operator, not a
        # LIKE '%...%' scan, so this stays fast as the person table grows and
        # tolerates typos the way "Search Existing Members" (Discovery Method 2)
        # needs to.
        sql = text(
            """
            SELECT id, first_name, last_name,
                   similarity(first_name || ' ' || last_name, :query) AS match_score
            FROM person
            WHERE (first_name || ' ' || last_name) % :query
            ORDER BY match_score DESC
            LIMIT :limit
            """
        )
        result = await self.session.execute(sql, {"query": query, "limit": limit})
        return [dict(row._mapping) for row in result]

    async def search_by_email(self, query: str, limit: int = 20) -> list[dict]:
        # A person is findable by whichever email is on record: their own
        # account email if they've claimed the profile, or the contact_email
        # left on an unclaimed one.
        sql = text(
            """
            SELECT DISTINCT p.id, p.first_name, p.last_name, 1.0 AS match_score
            FROM person p
            LEFT JOIN user_account ua ON ua.id = p.user_account_id
            WHERE lower(p.contact_email) LIKE lower(:pattern)
               OR lower(ua.email) LIKE lower(:pattern)
            LIMIT :limit
            """
        )
        result = await self.session.execute(sql, {"pattern": f"%{query}%", "limit": limit})
        return [dict(row._mapping) for row in result]
