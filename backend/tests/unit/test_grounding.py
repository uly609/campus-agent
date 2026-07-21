from __future__ import annotations

from app.agent.policies import synthesize_grounded_answer
from app.domain.schemas import Evidence


def test_grounding_refuses_without_evidence() -> None:
    answer = synthesize_grounded_answer("未知问题", [])
    assert "证据不足" in answer.answer
    assert answer.confidence == 0.0


def test_grounding_binds_claims_to_citations() -> None:
    evidence = [
        Evidence(
            evidence_id="ev1",
            source_id="doc1",
            source_type="official",
            title="图书馆",
            excerpt="图书馆 8:00-22:30 开放。",
            score=0.5,
            official=True,
            metadata={},
        )
    ]
    answer = synthesize_grounded_answer("图书馆几点关门", evidence)
    assert answer.claims[0].evidence_ids == ["ev1"]
    assert answer.citations[0].source_id == "doc1"

