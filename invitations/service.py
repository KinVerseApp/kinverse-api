from __future__ import annotations

import secrets
import string
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from profiles.repository import ProfileRepository
from shared.db_types import utcnow
from shared.exceptions import NotFoundError, ValidationError
from .models import Invitation
from .repository import InvitationRepository

VALID_METHODS = {"sms", "email", "link", "qr", "whatsapp"}
VALID_SCOPES = {"person", "tree"}


def _generate_invite_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "KIN-" + "".join(secrets.choice(alphabet) for _ in range(6))


def _detail(invitation: Invitation) -> dict:
    return {
        "id": invitation.id,
        "invite_code": invitation.invite_code,
        "method": invitation.method,
        "status": invitation.status,
        "expires_at": invitation.expires_at,
    }


class InvitationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = InvitationRepository(session)
        # Reused rather than duplicated - ProfileRepository already knows how
        # to fetch/update a Person, which accept_invitation needs to "claim"
        # an unclaimed relative once the invitee signs up.
        self.profile_repository = ProfileRepository(session)

    async def _create(self, user_id: UUID | str, payload: dict, method: str) -> dict:
        if method not in VALID_METHODS:
            raise ValidationError(f"method must be one of {sorted(VALID_METHODS)}")
        scope = payload.get("scope", "person")
        if scope not in VALID_SCOPES:
            raise ValidationError(f"scope must be one of {sorted(VALID_SCOPES)}")

        channel_value = payload.get("invitee_email") or payload.get("invitee_phone")
        invitation = Invitation(
            inviter_user_account_id=UUID(str(user_id)),
            invitee_person_id=payload.get("person_id"),
            scope=scope,
            method=method,
            channel_value=channel_value,
            invite_code=_generate_invite_code(),
            # A real channel to send through means it actually went out;
            # link/QR invites have no channel_value and stay 'pending' until
            # someone opens the link (§3.7 workflow: Invite Sent -> ...).
            status="sent" if channel_value else "pending",
        )
        created = await self.repository.add(invitation)
        return _detail(created)

    async def create_invitation(self, user_id: UUID | str, payload: dict) -> dict:
        return await self._create(user_id, payload, payload.get("method", "email"))

    async def send_email_invite(self, user_id: UUID | str, payload: dict) -> dict:
        return await self._create(user_id, payload, "email")

    async def send_sms_invite(self, user_id: UUID | str, payload: dict) -> dict:
        return await self._create(user_id, payload, "sms")

    async def generate_link(self, user_id: UUID | str, payload: dict) -> dict:
        return await self._create(user_id, payload, "link")

    async def generate_qr(self, user_id: UUID | str, payload: dict) -> dict:
        return await self._create(user_id, payload, "qr")

    async def _get_or_404(self, invite_id: UUID) -> Invitation:
        invitation = await self.repository.get_by_id(invite_id)
        if invitation is None:
            raise NotFoundError("Invitation", str(invite_id))
        return invitation

    async def accept_invitation(self, user_id: UUID | str, invite_id: UUID) -> dict:
        invitation = await self._get_or_404(invite_id)

        # Person-scoped invites "claim" the unclaimed Person the inviter
        # created (see profiles/service.py) - this is what turns a relative
        # added by hand into a full account without creating a duplicate node.
        if invitation.invitee_person_id is not None:
            person = await self.profile_repository.get_by_id(invitation.invitee_person_id)
            if person is not None:
                if person.user_account_id is not None and str(person.user_account_id) != str(user_id):
                    raise ValidationError("This invitation's person has already been claimed by someone else.")
                await self.profile_repository.update(person, {"user_account_id": UUID(str(user_id))})

        updated = await self.repository.update(
            invitation, {"status": "accepted", "responded_at": utcnow()}
        )
        return _detail(updated)

    async def decline_invitation(self, user_id: UUID | str, invite_id: UUID) -> dict:
        del user_id
        invitation = await self._get_or_404(invite_id)
        updated = await self.repository.update(
            invitation, {"status": "declined", "responded_at": utcnow()}
        )
        return _detail(updated)
