from __future__ import annotations

from app.domain.schemas import MemoryRecord
from app.retrieval.embeddings import cosine


def is_duplicate(candidate: MemoryRecord, existing: MemoryRecord) -> bool:
    if candidate.hash_value == existing.hash_value:
        return True
    if candidate.key == existing.key and cosine(candidate.embedding, existing.embedding) > 0.92:
        return True
    return False


def conflicts_with(candidate: MemoryRecord, existing: MemoryRecord) -> bool:
    if candidate.user_id != existing.user_id or candidate.key != existing.key:
        return False
    return candidate.value != existing.value and not is_duplicate(candidate, existing)

