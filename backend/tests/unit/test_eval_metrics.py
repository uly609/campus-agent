from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "evals"))

from eval_metrics import (  # type: ignore[import-not-found]
    binary_classification,
    fact_group_recall,
    multiclass_classification,
    retrieval_metrics,
)


def test_retrieval_metrics_use_rank_and_graded_relevance() -> None:
    scores = retrieval_metrics(["noise", "partial", "best"], {"best": 3, "partial": 1}, k=3)

    assert scores["hit_at_3"] == 1.0
    assert scores["precision_at_3"] == 2 / 3
    assert scores["recall_at_3"] == 1.0
    assert scores["mrr_at_3"] == 0.5
    assert 0.0 < scores["ndcg_at_3"] < 1.0


def test_binary_f1_does_not_confuse_accuracy_with_positive_class_quality() -> None:
    scores = binary_classification([True, True, False, False], [True, False, True, False])

    assert scores == {"accuracy": 0.5, "precision": 0.5, "recall": 0.5, "f1": 0.5}


def test_macro_f1_penalizes_an_unrecognized_intent() -> None:
    scores = multiclass_classification(
        ["campus_qa", "post_search", "post_search"],
        ["campus_qa", "campus_qa", "campus_qa"],
    )

    assert scores["accuracy"] == 1 / 3
    assert 0.0 < float(scores["macro_f1"]) < float(scores["accuracy"])


def test_fact_group_recall_requires_each_reference_fact() -> None:
    score = fact_group_recall(
        "图书馆普通周 22:30 闭馆。",
        [["22:30"], ["15 分钟", "15分钟"]],
    )

    assert score == 0.5
