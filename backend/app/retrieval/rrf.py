from __future__ import annotations

from collections import defaultdict
from typing import TypeVar

T = TypeVar("T")


def reciprocal_rank_fusion(rankings: list[list[tuple[str, T]]], k: int = 60) -> list[tuple[str, float, T]]:
    scores: defaultdict[str, float] = defaultdict(float)
    payloads: dict[str, T] = {}
    for ranking in rankings:
        seen: set[str] = set()
        for rank, (source_id, payload) in enumerate(ranking, start=1):
            if source_id in seen:
                continue
            seen.add(source_id)
            scores[source_id] += 1.0 / (k + rank)
            payloads.setdefault(source_id, payload)
    return sorted(
        [(source_id, score, payloads[source_id]) for source_id, score in scores.items()],
        key=lambda item: item[1],
        reverse=True,
    )

