from __future__ import annotations

from app.memory.conflict import conflicts_with, is_duplicate
from app.memory.extractor import extract_memories


def test_memory_hash_dedup_and_conflict() -> None:
    first = extract_memories("u1", "记住我喜欢安静自习室")[0]
    duplicate = extract_memories("u1", "记住我喜欢安静自习室")[0]
    changed = extract_memories("u1", "记住我喜欢靠窗自习室")[0]
    assert is_duplicate(first, duplicate)
    assert conflicts_with(changed, first)


def test_residence_statement_is_a_memory_but_generic_post_is_not() -> None:
    residence = extract_memories("u-residence", "我住在生活区西区")
    generic = extract_memories("u-residence", "生活区西区今晚举办活动")

    assert residence
    assert residence[0].value == "我住在生活区西区"
    assert generic == []
