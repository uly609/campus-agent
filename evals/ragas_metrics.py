from __future__ import annotations

import re
from typing import Iterable, Sequence

from eval_metrics import safe_div

STOP_TOKENS = frozenset(
    {
        "的",
        "了",
        "是",
        "我",
        "你",
        "他",
        "她",
        "它",
        "在",
        "有",
        "和",
        "与",
        "及",
        "为",
        "吗",
        "呢",
        "吧",
        "啊",
        "这",
        "那",
        "也",
        "都",
        "会",
        "要",
        "可",
        "以",
        "能",
        "对",
        "从",
        "到",
        "们",
        "被",
        "把",
        "让",
        "向",
        "由",
        "于",
        "或",
        "并",
        "但",
        "而",
        "其",
        "此",
        "之",
        "者",
        "the",
        "a",
        "an",
        "is",
        "are",
        "of",
        "and",
        "to",
        "in",
        "on",
        "for",
    }
)


def tokenize_for_metrics(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]", text.lower())
    return {token for token in tokens if token not in STOP_TOKENS}


def extract_claims(answer: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"[。！？!?;；\n]", answer) if part.strip()]
    claims: list[str] = []
    for part in parts:
        if len(part) >= 4 and part not in claims:
            claims.append(part)
    return claims


def claim_support_rate(claims: Sequence[str], evidence_texts: Iterable[str]) -> float:
    evidence_tokens = set()
    for text in evidence_texts:
        evidence_tokens |= tokenize_for_metrics(str(text))
    if not claims:
        return 1.0
    supported = 0
    for claim in claims:
        claim_tokens = tokenize_for_metrics(claim)
        if not claim_tokens:
            supported += 1
            continue
        overlap = len(claim_tokens.intersection(evidence_tokens))
        if overlap / len(claim_tokens) >= 0.5:
            supported += 1
    return safe_div(supported, len(claims))


def answer_relevancy_score(question: str, answer: str) -> float:
    question_tokens = tokenize_for_metrics(question)
    if not question_tokens:
        return 1.0
    answer_tokens = tokenize_for_metrics(answer)
    overlap = len(question_tokens.intersection(answer_tokens))
    return min(1.0, overlap / len(question_tokens))


def context_precision_score(
    evidence: Sequence[dict[str, object]],
    expected_sources: Iterable[str],
) -> float:
    expected = set(expected_sources)
    hits = [int(str(item.get("source_id", "")) in expected) for item in evidence]
    if not hits:
        return 0.0
    values = [sum(hits[: index + 1]) / (index + 1) for index, hit in enumerate(hits) if hit]
    return safe_div(sum(values), len(values))


def context_recall_score(
    evidence: Sequence[dict[str, object]],
    expected_sources: Iterable[str],
) -> float:
    expected = set(expected_sources)
    returned = {str(item.get("source_id", "")) for item in evidence}
    return safe_div(len(returned.intersection(expected)), len(expected))
