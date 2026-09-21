from __future__ import annotations


class SearchRepository:
    async def search(self, query: str) -> list[dict]:
        return [{"id": "1", "first_name": "Search", "last_name": "Result"}] if query else []
