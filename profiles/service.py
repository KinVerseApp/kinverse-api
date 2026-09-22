from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions import NotFoundError
from users.models import Person
from .repository import ProfileRepository


def _detail(person: Person) -> dict:
    return {
        "id": person.id,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "date_of_birth": person.date_of_birth,
        "gender": person.gender,
        "biography": person.biography,
        "profile_photo_url": person.profile_photo_url,
        "default_visibility": person.default_visibility,
    }


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProfileRepository(session)

    async def create_profile(self, user_id: UUID | str, payload: dict) -> dict:
        # Used for the "Add Relative" flow: the tree owner creates a brand-new,
        # unclaimed Person (no user_account_id yet) they know about but who
        # hasn't signed up. The caller then POSTs /relationships to link it in.
        # NOT used for a user's own registration profile - users/service.py
        # creates that Person directly so it can be wired to the new
        # UserAccount in the same transaction.
        person = Person(
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            date_of_birth=payload.get("date_of_birth"),
            gender=payload.get("gender"),
            biography=payload.get("biography"),
            default_visibility=payload.get("default_visibility", "family_network"),
            created_by_user_account_id=UUID(str(user_id)),
        )
        created = await self.repository.add(person)
        return _detail(created)

    async def _get_or_404(self, person_id: UUID) -> Person:
        person = await self.repository.get_by_id(person_id)
        if person is None:
            raise NotFoundError("Person", str(person_id))
        return person

    async def get_profile(self, user_id: UUID | str, person_id: UUID) -> dict:
        del user_id  # visibility filtering belongs here once the privacy module is real
        person = await self._get_or_404(person_id)
        return _detail(person)

    async def update_profile(self, user_id: UUID | str, person_id: UUID, payload: dict) -> dict:
        del user_id
        person = await self._get_or_404(person_id)
        updated = await self.repository.update(person, payload)
        return _detail(updated)

    async def upload_profile_image(self, user_id: UUID | str, person_id: UUID, file_name: str) -> dict:
        del user_id
        person = await self._get_or_404(person_id)
        # Real upload to Azure Blob Storage isn't wired up yet - shared/settings.py
        # already carries AZURE_STORAGE_* config but no client exists. This writes
        # a placeholder URL so the field round-trips correctly until that lands.
        placeholder_url = f"https://placeholder.blob.core.windows.net/profile-images/{person.id}/{file_name}"
        updated = await self.repository.update(person, {"profile_photo_url": placeholder_url})
        return {"profile_photo_url": updated.profile_photo_url}

    async def get_heritage(self, user_id: UUID | str, person_id: UUID) -> dict:
        del user_id
        person = await self._get_or_404(person_id)
        return {
            "native_country": person.native_country,
            "native_state": person.native_state,
            "native_district": person.native_district,
            "native_village": person.native_village,
        }

    async def update_heritage(self, user_id: UUID | str, person_id: UUID, payload: dict) -> dict:
        del user_id
        person = await self._get_or_404(person_id)
        updated = await self.repository.update(person, payload)
        return {
            "native_country": updated.native_country,
            "native_state": updated.native_state,
            "native_district": updated.native_district,
            "native_village": updated.native_village,
        }
