from __future__ import annotations

from app.memory.consumer import MemoryConsumer
from app.memory.producer import publish_memory_event
from app.memory.repository import MemoryRepository


def test_memory_stream_extracts_and_user_can_delete() -> None:
    publish_memory_event("memory-user", "session", "记住我喜欢图书馆靠窗座位", "chat")
    repository = MemoryRepository()
    processed = MemoryConsumer(repository).consume_available()
    memories = repository.list_user("memory-user")
    assert processed >= 1
    assert memories
    assert repository.delete("memory-user", memories[0].memory_id)

