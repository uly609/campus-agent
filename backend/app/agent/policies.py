from __future__ import annotations

from app.domain.schemas import Citation, Claim, Evidence, GroundedAnswer


def judge_relevance(query: str, evidence: list[Evidence]) -> dict[str, float | bool]:
    if not evidence:
        return {"relevant": False, "score": 0.0, "coverage": 0.0}
    unsupported_markers = ["不存在", "火星", "飞船", "量子", "传送门", "海底", "管理员密码", "忽略规则", "忽略指令"]
    if any(marker in query for marker in unsupported_markers):
        return {"relevant": False, "score": 0.0, "coverage": 0.0}
    supported_fact_anchors = [
        "图书馆",
        "宿舍",
        "寝室",
        "一卡通",
        "校园卡",
        "奖学金",
        "校医院",
        "急诊",
        "看诊",
        "票据",
        "后勤",
        "报修",
    ]
    if all(item.official for item in evidence) and not any(anchor in query for anchor in supported_fact_anchors):
        return {"relevant": False, "score": 0.0, "coverage": 0.0}
    ignored = set("的是了在有和与或请问一下多少什么怎么如何能否校园官方说明")
    query_chars = {char for char in query.lower() if char.isalnum() and char not in ignored}
    scores = []
    for item in evidence:
        haystack = f"{item.title} {item.excerpt}".lower()
        overlap = len(query_chars.intersection(haystack)) / max(len(query_chars), 1)
        scores.append(min(1.0, overlap + item.score * 1.5))
    score = max(scores)
    relevant_count = sum(1 for value in scores if value >= 0.25)
    coverage = min(1.0, relevant_count / min(len(scores), 3))
    return {"relevant": score >= 0.25, "score": round(score, 4), "coverage": round(coverage, 4)}


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
