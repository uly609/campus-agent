from __future__ import annotations

from typing import Any

from app.core.redis import get_redis_client
from app.memory.events import MemoryEvent
from app.memory.extractor import extract_memories
from app.memory.producer import STREAM_NAME
from app.memory.repository import MemoryRepository


class MemoryConsumer:
    def __init__(self, repository: MemoryRepository | None = None) -> None:
        self.repository = repository or MemoryRepository()

    def consume_available(self) -> int:
        client = get_redis_client()
        rows: list[tuple[str, dict[str, Any]]] = []
        if hasattr(client, "xrange"):
            raw_rows = client.xrange(STREAM_NAME)
            rows = [(row_id, fields) for row_id, fields in raw_rows]
        processed = 0
        for _row_id, fields in rows:
            event = MemoryEvent.model_validate(fields)
            for memory in extract_memories(event.user_id, event.text):
                self.repository.upsert(memory)
                processed += 1
        return processed

