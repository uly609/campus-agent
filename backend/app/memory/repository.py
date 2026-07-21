from __future__ import annotations

from app.domain.schemas import MemoryRecord
from app.memory.conflict import conflicts_with, is_duplicate
from app.services.repository import JsonRepository


class MemoryRepository:
    def __init__(self, repo: JsonRepository | None = None) -> None:
        self.repo = repo or JsonRepository()

    def upsert(self, candidate: MemoryRecord) -> MemoryRecord | None:
        existing = self.repo.load_memories(candidate.user_id)
        for memory in existing:
            if is_duplicate(candidate, memory):
                return memory
        for memory in existing:
            if conflicts_with(candidate, memory):
                candidate.supersedes = memory.memory_id
                break
        return self.repo.save_memory(candidate)

    def list_user(self, user_id: str) -> list[MemoryRecord]:
        return self.repo.load_memories(user_id)

    def delete(self, user_id: str, memory_id: str) -> bool:
        return self.repo.delete_memory(user_id, memory_id)

