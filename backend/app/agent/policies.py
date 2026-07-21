from __future__ import annotations

from app.domain.schemas import Citation, Claim, Evidence, GroundedAnswer


def judge_relevance(query: str, evidence: list[Evidence]) -> dict[str, float | bool]:
    if not evidence:
        return {"relevant": False, "score": 0.0, "coverage": 0.0}
    query_chars = set(query.lower())
    scores = []
    for item in evidence:
        haystack = f"{item.title} {item.excerpt}".lower()
        overlap = len(query_chars.intersection(haystack)) / max(len(query_chars), 1)
        scores.append(min(1.0, overlap + item.score * 6))
    score = max(scores)
    coverage = sum(1 for value in scores if value >= 0.25) / max(len(scores), 1)
    return {"relevant": score >= 0.2, "score": round(score, 4), "coverage": round(coverage, 4)}


def synthesize_grounded_answer(query: str, evidence: list[Evidence]) -> GroundedAnswer:
    official = [item for item in evidence if item.official]
    support = official or evidence
    if not support:
        return GroundedAnswer(
            answer="证据不足，我不能可靠回答这个校园事实问题。请换个问法或提供更多线索。",
            claims=[],
            citations=[],
            unsupported_questions=[query],
            confidence=0.0,
        )
    claims: list[Claim] = []
    citations: list[Citation] = []
    sentences = []
    for index, item in enumerate(support[:3], start=1):
        claim_id = f"claim-{index}"
        source_note = "官方信息" if item.official else "社区信息，可能过时"
        claim_text = f"{source_note}：{item.excerpt[:120]}"
        claims.append(Claim(claim_id=claim_id, text=claim_text, evidence_ids=[item.evidence_id]))
        citations.append(
            Citation(
                citation_id=f"cite-{index}",
                claim_id=claim_id,
                evidence_id=item.evidence_id,
                source_id=item.source_id,
                title=item.title,
            )
        )
        sentences.append(f"{claim_text} [{index}]")
    return GroundedAnswer(
        answer="\n".join(sentences),
        claims=claims,
        citations=citations,
        unsupported_questions=[],
        confidence=0.78 if official else 0.55,
    )

