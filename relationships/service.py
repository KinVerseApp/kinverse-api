from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared.db_types import utcnow
from shared.exceptions import NotFoundError, ValidationError
from users.repository import UserRepository
from .models import RelationshipEdge
from .repository import RelationshipRepository

VALID_EDGE_TYPES = {"parent_child", "partner"}
VALID_PARTNER_TYPES = {"spouse", "partner", "ex_spouse", "ex_partner"}


def _as_dict(edge: RelationshipEdge) -> dict:
    return {
        "id": edge.id,
        "person_a_id": edge.person_a_id,
        "person_b_id": edge.person_b_id,
        "edge_type": edge.edge_type,
        "status": edge.status,
        "source": edge.source,
        "partner_type": edge.partner_type,
    }


class RelationshipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = RelationshipRepository(session)
        self.user_repository = UserRepository(session)

    async def add_relative(self, user_id: UUID | str, payload: dict) -> dict:
        edge_type = payload.get("edge_type", "parent_child")
        if edge_type not in VALID_EDGE_TYPES:
            raise ValidationError(f"edge_type must be one of {sorted(VALID_EDGE_TYPES)}")

        person_a_id: UUID = payload["person_a_id"]
        person_b_id: UUID = payload["person_b_id"]
        partner_type = payload.get("partner_type")

        if edge_type == "partner":
            if partner_type not in VALID_PARTNER_TYPES:
                raise ValidationError(f"partner_type is required and must be one of {sorted(VALID_PARTNER_TYPES)}")
            # Partner edges are undirected — enforce the same canonical
            # (lower-uuid-first) ordering the DB CHECK constraint requires,
            # so (A, B) and (B, A) can never both be inserted.
            if str(person_a_id) > str(person_b_id):
                person_a_id, person_b_id = person_b_id, person_a_id
        else:
            partner_type = None  # DB CHECK forbids partner_type on parent_child edges

        # Manual adds (the tree owner adding a relative directly) are useful
        # immediately — there's no one else to confirm them yet, since the
        # relative is usually a brand-new unclaimed Person. Anything created
        # via a search match against an EXISTING claimed person needs the
        # other side's confirmation before it's treated as real (§3.6,
        # Discovery Method 2: "This is my relative" -> connection request).
        source = payload.get("source", "manual")
        status = "confirmed" if source == "manual" else "pending"

        edge = RelationshipEdge(
            person_a_id=person_a_id,
            person_b_id=person_b_id,
            edge_type=edge_type,
            partner_type=partner_type,
            status=status,
            source=source,
            start_date=payload.get("start_date"),
            created_by_user_account_id=UUID(str(user_id)),
        )
        created = await self.repository.add_edge(edge)
        return _as_dict(created)

    async def _get_or_404(self, relationship_id: UUID) -> RelationshipEdge:
        edge = await self.repository.get_by_id(relationship_id)
        if edge is None:
            raise NotFoundError("Relationship", str(relationship_id))
        return edge

    async def update_relationship(self, user_id: UUID | str, relationship_id: UUID, payload: dict) -> dict:
        del user_id  # ownership/permission check belongs here once roles are defined
        edge = await self._get_or_404(relationship_id)
        updated = await self.repository.update(edge, payload)
        return _as_dict(updated)

    async def confirm_relationship(self, user_id: UUID | str, relationship_id: UUID) -> dict:
        edge = await self._get_or_404(relationship_id)
        account = await self.user_repository.get_by_id(UUID(str(user_id)))
        person = await self.user_repository.get_person_by_user_id(account.id) if account else None
        updated = await self.repository.update(
            edge,
            {
                "status": "confirmed",
                "confirmed_at": utcnow(),
                "confirmed_by_person_id": person.id if person else None,
            },
        )
        return _as_dict(updated)

    async def reject_relationship(self, user_id: UUID | str, relationship_id: UUID) -> dict:
        del user_id
        edge = await self._get_or_404(relationship_id)
        updated = await self.repository.update(edge, {"status": "rejected"})
        return _as_dict(updated)

    async def remove_relationship(self, user_id: UUID | str, relationship_id: UUID) -> None:
        del user_id
        edge = await self._get_or_404(relationship_id)
        await self.repository.delete(edge)
