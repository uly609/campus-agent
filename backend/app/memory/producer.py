from __future__ import annotations

import uuid

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.memory.events import MemoryEvent
from app.services.repository import now_iso

STREAM_NAME = "campusflow:memory_events"


def publish_memory_event(user_id: str, session_id: str, text: str, source: str) -> str:
    if not get_settings().memory_enabled:
        return "memory-disabled"
    event = MemoryEvent(
        event_id=f"mev-{uuid.uuid4().hex[:12]}",
        user_id=user_id,
        session_id=session_id,
        source=source,
        text=text,
        created_at=now_iso(),
    )
    client = get_redis_client()
    return str(client.xadd(STREAM_NAME, event.model_dump(mode="json"), maxlen=1000, approximate=True))

