from __future__ import annotations

from app.domain.enums import Intent


def plan_intent(query: str, user_id: str) -> tuple[Intent, list[dict[str, object]], float]:
    lowered = query.lower()
    if any(word in lowered for word in ["你好", "您好", "嗨", "hello", "hi"]):
        return Intent.GREETING, [], 0.96
    if any(word in lowered for word in ["起草", "发帖", "草稿", "写一篇", "帮我写"]):
        return Intent.POST_DRAFT, [{"tool": "create_post_draft", "args": {"intent": query}}], 0.92
    if any(card in lowered for card in ["一卡通", "校园卡"]) and any(action in lowered for action in ["挂失", "补办", "补卡"]):
        return (
            Intent.CAMPUS_QA,
            [
                {"tool": "search_campus_docs", "args": {"query": query}},
                {"tool": "get_campus_service_info", "args": {"query": query}},
            ],
            0.95,
        )
    if any(word in lowered for word in ["失物", "招领", "捡到", "丢了", "遗失", "找回"]):
        return (
            Intent.LOST_FOUND,
            [
                {"tool": "search_lost_and_found", "args": {"query": query}},
                {"tool": "search_posts", "args": {"query": query}},
            ],
            0.92,
        )
    if any(word in lowered for word in ["记住", "记忆", "偏好", "忘掉", "删除记忆"]):
        return Intent.MEMORY, [{"tool": "load_user_memories", "args": {"user_id": user_id}}], 0.91
    if any(word in lowered for word in ["评测", "评估报告", "eval", "指标报告"]):
        return Intent.EVAL, [{"tool": "get_eval_report", "args": {}}], 0.9
    if any(word in lowered for word in ["帖子", "搜索", "二手", "拼车", "活动", "社区里"]):
        return Intent.POST_SEARCH, [{"tool": "search_posts", "args": {"query": query}}], 0.88
    return (
        Intent.CAMPUS_QA,
        [
            {"tool": "search_campus_docs", "args": {"query": query}},
            {"tool": "get_campus_service_info", "args": {"query": query}},
        ],
        0.84,
    )
