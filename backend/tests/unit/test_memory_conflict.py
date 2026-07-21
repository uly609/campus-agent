from __future__ import annotations

from app.memory.conflict import conflicts_with, is_duplicate
from app.memory.extractor import extract_memories


def test_memory_hash_dedup_and_conflict() -> None:
    first = extract_memories("u1", "记住我喜欢安静自习室")[0]
    duplicate = extract_memories("u1", "记住我喜欢安静自习室")[0]
    changed = extract_memories("u1", "记住我喜欢靠窗自习室")[0]
    assert is_duplicate(first, duplicate)
    assert conflicts_with(changed, first)

