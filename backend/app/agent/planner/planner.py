from __future__ import annotations

from app.agent.planner.schemas import IntentPlan, ToolCall
from app.agent.planner.validator import PlanValidator
from app.domain.enums import Intent


DEFAULT_PLANNER_TOOLS = frozenset(
    {
        "create_post_draft",
        "get_campus_service_info",
        "get_eval_report",
        "load_user_memories",
        "search_campus_docs",
        "search_lost_and_found",
        "search_posts",
    }
)


class StructuredPlanner:
    def __init__(self, validator: PlanValidator | None = None) -> None:
        self.validator = validator or PlanValidator(DEFAULT_PLANNER_TOOLS)

    def plan(self, query: str, user_id: str) -> IntentPlan:
        return self.validator.validate(self._fallback_plan(query, user_id))

    @staticmethod
    def _fallback_plan(query: str, user_id: str) -> IntentPlan:
        lowered = query.lower()
        if any(word in lowered for word in ["你好", "您好", "嗨", "hello", "hi"]):
            return IntentPlan(intent=Intent.GREETING, tool_calls=[], confidence=0.96, source="fallback")
        if any(word in lowered for word in ["起草", "发帖", "草稿", "写一篇", "帮我写"]):
            return IntentPlan(
                intent=Intent.POST_DRAFT,
                tool_calls=[ToolCall(tool_name="create_post_draft", arguments={"intent": query})],
                confidence=0.92,
                source="fallback",
            )
        if any(card in lowered for card in ["一卡通", "校园卡"]) and any(
            action in lowered for action in ["挂失", "补办", "补卡"]
        ):
            return IntentPlan(
                intent=Intent.CAMPUS_QA,
                tool_calls=[
                    ToolCall(tool_name="search_campus_docs", arguments={"query": query}),
                    ToolCall(tool_name="get_campus_service_info", arguments={"query": query}),
                ],
                confidence=0.95,
                source="fallback",
            )
        if any(word in lowered for word in ["失物", "招领", "捡到", "丢了", "遗失", "找回"]):
            return IntentPlan(
                intent=Intent.LOST_FOUND,
                tool_calls=[
                    ToolCall(tool_name="search_lost_and_found", arguments={"query": query}),
                    ToolCall(tool_name="search_posts", arguments={"query": query}),
                ],
                confidence=0.92,
                source="fallback",
            )
        if any(word in lowered for word in ["记住", "记忆", "偏好", "忘掉", "删除记忆"]):
            return IntentPlan(
                intent=Intent.MEMORY,
                tool_calls=[ToolCall(tool_name="load_user_memories", arguments={"user_id": user_id})],
                confidence=0.91,
                source="fallback",
            )
        if any(word in lowered for word in ["评测", "评估报告", "eval", "指标报告"]):
            return IntentPlan(
                intent=Intent.EVAL,
                tool_calls=[ToolCall(tool_name="get_eval_report", arguments={})],
                confidence=0.9,
                source="fallback",
            )
        if any(word in lowered for word in ["帖子", "搜索", "二手", "拼车", "活动", "社区里"]):
            return IntentPlan(
                intent=Intent.POST_SEARCH,
                tool_calls=[ToolCall(tool_name="search_posts", arguments={"query": query})],
                confidence=0.88,
                source="fallback",
            )
        return IntentPlan(
            intent=Intent.CAMPUS_QA,
            tool_calls=[
                ToolCall(tool_name="search_campus_docs", arguments={"query": query}),
                ToolCall(tool_name="get_campus_service_info", arguments={"query": query}),
            ],
            confidence=0.84,
            source="fallback",
        )
