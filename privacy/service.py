from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from profiles.repository import ProfileRepository
from shared.exceptions import NotFoundError, ValidationError
from users.repository import UserRepository
from .repository import PrivacyRepository

VALID_FIELDS = {"email", "phone", "date_of_birth", "address", "heritage_info", "biography"}
VALID_VISIBILITY = {"public", "family_network", "direct_relatives", "private"}


class PrivacyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = PrivacyRepository(session)
        # Reused, not duplicated: ProfileRepository already knows how to fetch
        # a Person by id, and UserRepository already knows how to resolve
        # "the current user's own Person" - the same helper tree/service.py uses.
        self.profile_repository = ProfileRepository(session)
        self.user_repository = UserRepository(session)

    async def _resolve_person(self, user_id: UUID | str, person_id: UUID | None):
        if person_id is not None:
            person = await self.profile_repository.get_by_id(person_id)
            if person is None:
                raise NotFoundError("Person", str(person_id))
            return person
        account = await self.user_repository.get_by_id(UUID(str(user_id)))
        if account is None:
            raise NotFoundError("User", str(user_id))
        person = await self.user_repository.get_person_by_user_id(account.id)
        if person is None:
            raise NotFoundError("Person for user", str(user_id))
        return person

    async def get_privacy_settings(self, user_id: UUID | str, person_id: UUID | None = None) -> list[dict]:
        person = await self._resolve_person(user_id, person_id)
        configured = {
            row.field_key: row.visibility for row in await self.repository.list_for_person(person.id)
        }
        # Every field the app can show a toggle for comes back, even if it
        # was never explicitly set - falling back to the person's
        # default_visibility, exactly like an absent row is documented to
        # behave in kinverse_schema.sql.
        return [
            {"field_key": field, "visibility": configured.get(field, person.default_visibility)}
            for field in sorted(VALID_FIELDS)
        ]

    async def update_privacy_settings(
        self, user_id: UUID | str, payload: dict, person_id: UUID | None = None
    ) -> list[dict]:
        person = await self._resolve_person(user_id, person_id)
        for item in payload.get("settings", []):
            field_key = item["field_key"]
            visibility = item["visibility"]
            if field_key not in VALID_FIELDS:
                raise ValidationError(f"field_key must be one of {sorted(VALID_FIELDS)}")
            if visibility not in VALID_VISIBILITY:
                raise ValidationError(f"visibility must be one of {sorted(VALID_VISIBILITY)}")
            await self.repository.upsert(person.id, field_key, visibility)
        return await self.get_privacy_settings(user_id, person.id)

    async def get_visibility_filter(self, user_id: UUID | str) -> dict:
        person = await self._resolve_person(user_id, None)
        return {"visibility": person.default_visibility}
