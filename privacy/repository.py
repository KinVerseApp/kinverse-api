from __future__ import annotations


class PrivacyRepository:
    async def list_settings(self, person_id: str) -> list[dict]:
        del person_id
        return []
