from __future__ import annotations

from app.retrieval.rrf import reciprocal_rank_fusion


def test_rrf_promotes_items_seen_by_multiple_retrievers() -> None:
    fused = reciprocal_rank_fusion(
        [
            [("a", {"name": "a"}), ("b", {"name": "b"})],
            [("c", {"name": "c"}), ("b", {"name": "b"})],
            [("b", {"name": "b"}), ("a", {"name": "a"})],
        ],
        k=60,
    )
    assert fused[0][0] == "b"


def test_rrf_deduplicates_within_single_ranking() -> None:
    fused = reciprocal_rank_fusion([[("a", 1), ("a", 2)], [("b", 3)]], k=60)
    assert [item[0] for item in fused].count("a") == 1

