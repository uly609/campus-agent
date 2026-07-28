from __future__ import annotations

from app.domain.enums import MemoryType
from app.domain.schemas import MemoryRecord
from app.memory.recall import recall_relevant_memories
from app.retrieval.embeddings import embed_text


def memory(value: str) -> MemoryRecord:
    return MemoryRecord(
        memory_id="m-" + value,
        user_id="u1",
        memory_type=MemoryType.FACT,
        key="fact",
        value=value,
        hash_value=value,
        embedding=embed_text(value),
        created_at="2026-01-01T00:00:00+00:00",
    )


def test_semantic_memory_recall_returns_related_top_k() -> None:
    rows = recall_relevant_memories(
        "推荐离生活区西区近的自习室", [memory("我住在生活区西区"), memory("我喜欢打篮球")]
    )
    assert rows
    assert rows[0]["value"] == "我住在生活区西区"
    assert rows[0]["recall_score"] > 0
