from __future__ import annotations

import json
import pytest

from app.agent.grounded_llm import parse_grounded_model_output
from app.domain.schemas import Evidence

EVIDENCE = Evidence(
    evidence_id="ev-1",
    source_id="doc-1",
    source_type="official",
    title="图书馆通知",
    excerpt="图书馆工作日开放至晚上十点。",
    score=0.9,
    official=True,
)


def test_exact_quote_is_preserved_in_citation() -> None:
    answer = parse_grounded_model_output(
        json.dumps(
            {
                "claims": [
                    {
                        "text": "图书馆开放至晚上十点",
                        "evidence_id": "ev-1",
                        "quoted_span": "图书馆工作日开放至晚上十点",
                    }
                ]
            }
        ),
        [EVIDENCE],
    )
    assert answer.citations[0].quoted_span == "图书馆工作日开放至晚上十点"


def test_non_verbatim_quote_is_rejected() -> None:
    with pytest.raises(ValueError, match="verbatim"):
        parse_grounded_model_output(
            json.dumps(
                {
                    "claims": [
                        {
                            "text": "图书馆开放至晚上十点",
                            "evidence_id": "ev-1",
                            "quoted_span": "图书馆每天二十四小时开放",
                        }
                    ]
                }
            ),
            [EVIDENCE],
        )
