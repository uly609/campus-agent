from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def binary_classification(expected: Sequence[bool], predicted: Sequence[bool]) -> dict[str, float]:
    if len(expected) != len(predicted):
        raise ValueError("expected and predicted must have the same length")
    tp = sum(want and got for want, got in zip(expected, predicted))
    fp = sum(not want and got for want, got in zip(expected, predicted))
    fn = sum(want and not got for want, got in zip(expected, predicted))
    tn = sum(not want and not got for want, got in zip(expected, predicted))
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    return {
        "accuracy": safe_div(tp + tn, len(expected)),
        "precision": precision,
        "recall": recall,
        "f1": safe_div(2 * precision * recall, precision + recall),
    }


def multiclass_classification(expected: Sequence[str], predicted: Sequence[str]) -> dict[str, object]:
    if len(expected) != len(predicted):
        raise ValueError("expected and predicted must have the same length")
    labels = sorted(set(expected) | set(predicted))
    per_class: dict[str, dict[str, float]] = {}
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for want, got in zip(expected, predicted):
        confusion[want][got] += 1
    for label in labels:
        scores = binary_classification(
            [item == label for item in expected],
            [item == label for item in predicted],
        )
        per_class[label] = {key: scores[key] for key in ("precision", "recall", "f1")}
    return {
        "accuracy": safe_div(sum(want == got for want, got in zip(expected, predicted)), len(expected)),
        "macro_precision": safe_div(sum(item["precision"] for item in per_class.values()), len(labels)),
        "macro_recall": safe_div(sum(item["recall"] for item in per_class.values()), len(labels)),
        "macro_f1": safe_div(sum(item["f1"] for item in per_class.values()), len(labels)),
        "per_class": per_class,
        "confusion_matrix": {label: dict(confusion[label]) for label in labels},
    }


def retrieval_metrics(ranked_ids: Sequence[str], qrels: Mapping[str, int], k: int = 8) -> dict[str, float]:
    ranked = list(dict.fromkeys(ranked_ids))[:k]
    relevant = {source_id for source_id, grade in qrels.items() if grade > 0}
    binary = [1 if source_id in relevant else 0 for source_id in ranked]
    precision = safe_div(sum(binary), k)
    recall = safe_div(sum(binary), len(relevant))
    reciprocal_rank = next((1.0 / rank for rank, hit in enumerate(binary, 1) if hit), 0.0)

    precision_sum = 0.0
    hits = 0
    for rank, hit in enumerate(binary, 1):
        if hit:
            hits += 1
            precision_sum += hits / rank
    average_precision = safe_div(precision_sum, min(len(relevant), k))

    gains = [qrels.get(source_id, 0) for source_id in ranked]
    dcg = sum((2**gain - 1) / math.log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal = sorted(qrels.values(), reverse=True)[:k]
    idcg = sum((2**gain - 1) / math.log2(rank + 1) for rank, gain in enumerate(ideal, 1))
    return {
        f"precision_at_{k}": precision,
        f"recall_at_{k}": recall,
        f"mrr_at_{k}": reciprocal_rank,
        f"map_at_{k}": average_precision,
        f"ndcg_at_{k}": safe_div(dcg, idcg),
        f"hit_at_{k}": float(bool(hits)),
    }


def fact_group_recall(answer: str, fact_groups: Sequence[Sequence[str]]) -> float:
    if not fact_groups:
        return 1.0
    normalized_answer = normalize_text(answer)
    matched = sum(
        any(normalize_text(alternative) in normalized_answer for alternative in group)
        for group in fact_groups
    )
    return safe_div(matched, len(fact_groups))


def citation_support_rate(
    answer: str,
    citations: Sequence[Mapping[str, object]],
    evidence: Sequence[Mapping[str, object]],
) -> float:
    if not citations:
        return 0.0
    by_id = {str(item.get("evidence_id")): item for item in evidence}
    answer_chars = content_chars(answer)
    supported = 0
    for citation in citations:
        item = by_id.get(str(citation.get("evidence_id")))
        if item is None:
            continue
        evidence_chars = content_chars(str(item.get("excerpt", "")))
        overlap = safe_div(len(answer_chars & evidence_chars), len(answer_chars))
        if overlap >= 0.45:
            supported += 1
    return safe_div(supported, len(citations))


def forbidden_term_rate(answer: str, terms: Iterable[str]) -> float:
    terms_list = list(terms)
    if not terms_list:
        return 0.0
    return safe_div(sum(term in answer for term in terms_list), len(terms_list))


def normalize_text(value: str) -> str:
    return re.sub(r"[\W_]", "", value.lower(), flags=re.UNICODE)


def content_chars(value: str) -> set[str]:
    ignored = set("的是了在有和与或及为对把被一个本条信息官方社区可能过时证据")
    return {char for char in normalize_text(value) if char not in ignored}
