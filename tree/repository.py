from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# These queries are the parameterized form of the ones validated against a
# live Postgres instance with a seeded sample tree in kinship_queries.sql
# (kinverse-project repo). Only parent_child + partner edges are read —
# every relationship label here is derived, never stored.


class TreeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_person(self, person_id: UUID) -> dict | None:
        result = await self.session.execute(
            text("SELECT id, first_name, last_name FROM person WHERE id = :person_id"),
            {"person_id": str(person_id)},
        )
        row = result.first()
        return dict(row._mapping) if row else None

    async def get_ancestors(self, person_id: UUID) -> list[dict]:
        """depth 1 = parent, depth 2 = grandparent, ..."""
        query = text(
            """
            WITH RECURSIVE ancestors AS (
                SELECT person_a_id AS person_id, 1 AS depth
                FROM relationship_edge
                WHERE edge_type = 'parent_child' AND status = 'confirmed'
                  AND person_b_id = :person_id
                UNION ALL
                SELECT re.person_a_id, a.depth + 1
                FROM relationship_edge re
                JOIN ancestors a ON re.person_b_id = a.person_id
                WHERE re.edge_type = 'parent_child' AND re.status = 'confirmed'
            )
            SELECT p.id, p.first_name, p.last_name, a.depth
            FROM ancestors a JOIN person p ON p.id = a.person_id
            ORDER BY a.depth
            """
        )
        result = await self.session.execute(query, {"person_id": str(person_id)})
        return [dict(row._mapping) for row in result]

    async def get_descendants(self, person_id: UUID) -> list[dict]:
        query = text(
            """
            WITH RECURSIVE descendants AS (
                SELECT person_b_id AS person_id, 1 AS depth
                FROM relationship_edge
                WHERE edge_type = 'parent_child' AND status = 'confirmed'
                  AND person_a_id = :person_id
                UNION ALL
                SELECT re.person_b_id, d.depth + 1
                FROM relationship_edge re
                JOIN descendants d ON re.person_a_id = d.person_id
                WHERE re.edge_type = 'parent_child' AND re.status = 'confirmed'
            )
            SELECT p.id, p.first_name, p.last_name, d.depth
            FROM descendants d JOIN person p ON p.id = d.person_id
            ORDER BY d.depth
            """
        )
        result = await self.session.execute(query, {"person_id": str(person_id)})
        return [dict(row._mapping) for row in result]

    async def get_siblings(self, person_id: UUID) -> list[dict]:
        query = text(
            """
            SELECT p.id, p.first_name, p.last_name,
                   COUNT(*) AS shared_parents,
                   CASE WHEN COUNT(*) >= 2 THEN 'full_sibling' ELSE 'half_sibling' END AS label
            FROM relationship_edge mine
            JOIN relationship_edge theirs
              ON mine.person_a_id = theirs.person_a_id
             AND mine.edge_type = 'parent_child' AND theirs.edge_type = 'parent_child'
             AND mine.status = 'confirmed' AND theirs.status = 'confirmed'
             AND theirs.person_b_id <> mine.person_b_id
            JOIN person p ON p.id = theirs.person_b_id
            WHERE mine.person_b_id = :person_id
            GROUP BY p.id, p.first_name, p.last_name
            """
        )
        result = await self.session.execute(query, {"person_id": str(person_id)})
        return [dict(row._mapping) for row in result]

    async def get_partner(self, person_id: UUID) -> dict | None:
        query = text(
            """
            SELECT p.id, p.first_name, p.last_name, re.partner_type
            FROM relationship_edge re
            JOIN person p ON p.id = CASE WHEN re.person_a_id = :person_id THEN re.person_b_id ELSE re.person_a_id END
            WHERE re.edge_type = 'partner' AND re.status = 'confirmed' AND re.end_date IS NULL
              AND :person_id IN (re.person_a_id, re.person_b_id)
            LIMIT 1
            """
        )
        result = await self.session.execute(query, {"person_id": str(person_id)})
        row = result.first()
        return dict(row._mapping) if row else None

    async def completeness_counts(self, person_id: UUID) -> dict:
        query = text(
            """
            SELECT
              EXISTS (
                SELECT 1 FROM relationship_edge
                WHERE edge_type = 'parent_child' AND status = 'confirmed' AND person_b_id = :person_id
              ) AS has_parent,
              EXISTS (
                SELECT 1 FROM relationship_edge mine
                JOIN relationship_edge theirs
                  ON mine.person_a_id = theirs.person_a_id AND theirs.person_b_id <> mine.person_b_id
                WHERE mine.edge_type = 'parent_child' AND theirs.edge_type = 'parent_child'
                  AND mine.status = 'confirmed' AND theirs.status = 'confirmed'
                  AND mine.person_b_id = :person_id
              ) AS has_sibling,
              EXISTS (
                SELECT 1 FROM relationship_edge
                WHERE edge_type = 'partner' AND status = 'confirmed'
                  AND :person_id IN (person_a_id, person_b_id)
              ) AS has_spouse,
              EXISTS (
                SELECT 1 FROM relationship_edge
                WHERE edge_type = 'parent_child' AND status = 'confirmed' AND person_a_id = :person_id
              ) AS has_child
            """
        )
        result = await self.session.execute(query, {"person_id": str(person_id)})
        row = result.first()
        return dict(row._mapping) if row else {}
