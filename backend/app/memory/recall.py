from __future__ import annotations

from app.domain.schemas import MemoryRecord
from app.retrieval.embeddings import cosine, embed_text


def recall_relevant_memories(
    query: str, memories: list[MemoryRecord], top_k: int = 3, min_score: float = 0.08
) -> list[dict[str, object]]:
    ranked: list[tuple[float, MemoryRecord]] = []
    for memory in memories:
        vector = memory.embedding or embed_text(memory.value)
        query_vector = embed_text(query)[: len(vector)]
        score = cosine(query_vector, vector)
        if score >= min_score:
            ranked.append((score, memory))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [
        {**memory.model_dump(mode="json"), "recall_score": round(score, 6)}
        for score, memory in ranked[:top_k]
    ]
