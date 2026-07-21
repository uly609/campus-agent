from __future__ import annotations

from pydantic import BaseModel, Field


class MemoryEvent(BaseModel):
    event_id: str
    user_id: str
    session_id: str
    source: str
    text: str = Field(max_length=2000)
    created_at: str
    expires_at: str | None = None

