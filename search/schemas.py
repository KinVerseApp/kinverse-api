from __future__ import annotations

from pydantic import BaseModel


class SearchResult(BaseModel):
    id: str
    first_name: str
    last_name: str
    match_score: float | None = None
