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


def test_grounding_uses_minimal_sufficient_evidence() -> None:
    evidence = [
        Evidence(
            evidence_id="ev-repair",
            source_id="doc-repair",
            source_type="official",
            title="宿舍维修流程",
            excerpt="宿舍漏水请提交后勤报修单，通常 24 小时内响应。",
            score=0.9,
            official=True,
            metadata={},
        ),
        Evidence(
            evidence_id="ev-network",
            source_id="doc-network",
            source_type="official",
            title="宿舍网络",
            excerpt="宿舍网络故障请提交网络报修单。",
            score=0.4,
            official=True,
            metadata={},
        ),
    ]
    answer = synthesize_grounded_answer("宿舍漏水找谁报修", evidence)
    assert [citation.source_id for citation in answer.citations] == ["doc-repair"]
