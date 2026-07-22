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
