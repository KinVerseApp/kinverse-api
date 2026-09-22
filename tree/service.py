from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import NotFoundError
from users.repository import UserRepository
from .repository import TreeRepository

_ANCESTOR_LABELS = {1: "parent", 2: "grandparent", 3: "great-grandparent"}
_DESCENDANT_LABELS = {1: "child", 2: "grandchild", 3: "great-grandchild"}


def _label_for_depth(depth: int, table: dict[int, str]) -> str:
    if depth in table:
        return table[depth]
    greats = depth - 2
    prefix = "great-" * max(greats, 0)
    return f"{prefix}grandparent" if table is _ANCESTOR_LABELS else f"{prefix}grandchild"


class TreeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TreeRepository(session)
        self.user_repository = UserRepository(session)

    async def _resolve_root(self, user_id: UUID | str, root_id: UUID | None) -> UUID:
        if root_id is not None:
            return root_id
        account = await self.user_repository.get_by_id(UUID(str(user_id)))
        if account is None:
            raise NotFoundError("User", str(user_id))
        person = await self.user_repository.get_person_by_user_id(account.id)
        if person is None:
            raise NotFoundError("Person for user", str(user_id))
        return person.id

    async def get_tree(self, user_id: UUID | str, root_id: UUID | None = None, limit: int = 50) -> dict:
        root_id = await self._resolve_root(user_id, root_id)

        root_person = await self.repository.get_person(root_id)
        if root_person is None:
            raise NotFoundError("Person", str(root_id))

        ancestors = await self.repository.get_ancestors(root_id)
        descendants = await self.repository.get_descendants(root_id)
        partner = await self.repository.get_partner(root_id)

        nodes: list[dict] = [
            {
                "id": root_id,
                "first_name": root_person["first_name"],
                "last_name": root_person["last_name"],
                "relationship": "you",
                "children": [],
            }
        ]
        for a in ancestors:
            nodes.append(
                {
                    "id": a["id"],
                    "first_name": a["first_name"],
                    "last_name": a["last_name"],
                    "relationship": _label_for_depth(a["depth"], _ANCESTOR_LABELS),
                    "children": [],
                }
            )
        for d in descendants:
            nodes.append(
                {
                    "id": d["id"],
                    "first_name": d["first_name"],
                    "last_name": d["last_name"],
                    "relationship": _label_for_depth(d["depth"], _DESCENDANT_LABELS),
                    "children": [],
                }
            )
        if partner:
            nodes.append(
                {
                    "id": partner["id"],
                    "first_name": partner["first_name"],
                    "last_name": partner["last_name"],
                    "relationship": partner["partner_type"] or "partner",
                    "children": [],
                }
            )

        nodes = nodes[:limit]
        return {"root_id": root_id, "nodes": nodes, "total_visible": len(nodes)}

    async def get_ancestors(self, person_id: UUID) -> list[dict]:
        rows = await self.repository.get_ancestors(person_id)
        return [
            {
                "id": str(r["id"]),
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "relationship": _label_for_depth(r["depth"], _ANCESTOR_LABELS),
            }
            for r in rows
        ]

    async def get_descendants(self, person_id: UUID) -> list[dict]:
        rows = await self.repository.get_descendants(person_id)
        return [
            {
                "id": str(r["id"]),
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "relationship": _label_for_depth(r["depth"], _DESCENDANT_LABELS),
            }
            for r in rows
        ]

    async def get_siblings(self, person_id: UUID) -> list[dict]:
        rows = await self.repository.get_siblings(person_id)
        return [
            {
                "id": str(r["id"]),
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "relationship": r["label"],
            }
            for r in rows
        ]

    async def get_family_completeness_score(self, user_id: UUID | str, person_id: UUID) -> dict:
        del user_id
        counts = await self.repository.completeness_counts(person_id)
        if not counts:
            return {"score": 0.0, "coverage": "not_available"}
        total = len(counts)
        achieved = sum(1 for v in counts.values() if v)
        score = round(achieved / total, 2)
        coverage = ", ".join(key.replace("has_", "") for key, v in counts.items() if v) or "none yet"
        return {"score": score, "coverage": coverage}
