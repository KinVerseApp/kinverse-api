from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationSummary(BaseModel):
    id: UUID
    type: str
    payload: dict
    is_read: bool = False
    created_at: datetime
