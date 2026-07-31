from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "evals"))

from ragas_metrics import (  # type: ignore[import-not-found]
    answer_relevancy_score,
    claim_support_rate,
    context_precision_score,
    context_recall_score,
    extract_claims,
)


def test_claim_support_rate_uses_evidence_tokens() -> None:
    claims = ["图书馆八点开门", "食堂在图书馆旁边"]
    assert claim_support_rate(claims, ["图书馆八点开门，食堂在图书馆旁边"]) == 1.0
    assert claim_support_rate(claims, ["完全无关的内容"]) == 0.0


def test_answer_relevancy_uses_question_tokens() -> None:
    assert answer_relevancy_score("图书馆几点关门", "图书馆晚上十点关门") == pytest.approx(6 / 7)
    assert answer_relevancy_score("图书馆几点关门", "今天是晴天") == 0.0


def test_context_precision_weights_earlier_hits() -> None:
    evidence = [
        {"source_id": "a"},
        {"source_id": "b"},
        {"source_id": "c"},
    ]
    assert context_precision_score(evidence, ["b", "c"]) == pytest.approx((0.5 + 0.6667) / 2, abs=0.001)
    assert context_precision_score(evidence, ["a"]) == 1.0


def test_context_recall_measures_coverage() -> None:
    evidence = [{"source_id": "a"}, {"source_id": "b"}]
    assert context_recall_score(evidence, ["a", "b", "c"]) == pytest.approx(2 / 3)


def test_extract_claims_splits_sentences() -> None:
    claims = extract_claims("图书馆八点开门。食堂在旁边。")
    assert len(claims) == 2
