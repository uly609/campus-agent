from __future__ import annotations

import json

import pytest

from app.agent.grounded_llm import parse_grounded_model_output
from app.domain.schemas import Evidence


def evidence() -> list[Evidence]:
    return [
        Evidence(
            evidence_id="ev-library",
            source_id="doc-library-hours-00",
            source_type="official",
            title="图书馆开放时间",
            excerpt="图书馆每天开放到 22:30。",
            score=0.9,
            official=True,
            metadata={},
        )
    ]


def test_model_claims_are_bound_to_supplied_evidence() -> None:
    content = json.dumps({"claims": [{"text": "图书馆每天开放到 22:30。", "evidence_id": "ev-library"}]}, ensure_ascii=False)
    answer = parse_grounded_model_output(content, evidence())
    assert answer.citations[0].source_id == "doc-library-hours-00"


def test_model_cannot_cite_unknown_evidence() -> None:
    content = json.dumps({"claims": [{"text": "图书馆每天开放到 22:30。", "evidence_id": "ev-unknown"}]}, ensure_ascii=False)
    with pytest.raises(ValueError, match="outside"):
        parse_grounded_model_output(content, evidence())


def test_model_must_answer_requested_query_facet() -> None:
    canteen = Evidence(
        evidence_id="ev-canteen",
        source_id="doc-canteen",
        source_type="official",
        title="学生食堂服务",
        excerpt="二食堂位于宿舍区南侧，晚餐供应到 19:30。",
        score=0.9,
        official=True,
        metadata={},
    )
    content = json.dumps(
        {"claims": [{"text": "二食堂晚餐供应到 19:30。", "evidence_id": "ev-canteen"}]},
        ensure_ascii=False,
    )
    with pytest.raises(ValueError, match="facet"):
        parse_grounded_model_output(content, [canteen], "二食堂在哪里")


def test_duplicate_model_claims_are_collapsed() -> None:
    content = json.dumps(
        {
            "claims": [
                {"text": "图书馆每天开放到 22:30。", "evidence_id": "ev-library"},
                {"text": "图书馆每天开放到 22:30。", "evidence_id": "ev-library"},
            ]
        },
        ensure_ascii=False,
    )
    answer = parse_grounded_model_output(content, evidence())
    assert len(answer.claims) == 1
    assert len(answer.citations) == 1


def test_distinct_claims_from_same_source_share_one_display_marker() -> None:
    content = json.dumps(
        {
            "claims": [
                {"text": "图书馆每天开放到 22:30。", "evidence_id": "ev-library"},
                {"text": "图书馆开放时间是每天到 22:30。", "evidence_id": "ev-library"},
            ]
        },
        ensure_ascii=False,
    )
    answer = parse_grounded_model_output(content, evidence())
    assert len(answer.claims) == 2
    assert len(answer.citations) == 2
    assert answer.answer.count("[1]") == 2
    assert "[2]" not in answer.answer
