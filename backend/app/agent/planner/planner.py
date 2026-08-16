from __future__ import annotations

import json

from app.agent.planner.schemas import IntentPlan, ToolCall
from app.agent.planner.validator import PlanValidator
from app.domain.enums import Intent
from app.llm.base import ProviderRecoverableError
from app.llm.router import ProviderRouter


DEFAULT_PLANNER_TOOLS = frozenset(
    {
        "create_post_draft",
        "get_knowledge_service_info",
        "get_eval_report",
        "load_user_memories",
        "search_knowledge_base",
        "search_lost_and_found",
        "search_posts",
        "search_official_web",
    }
)


class StructuredPlanner:
    def __init__(
        self,
        validator: PlanValidator | None = None,
        router: ProviderRouter | None = None,
        skills: object | None = None,
    ) -> None:
        self.validator = validator or PlanValidator(DEFAULT_PLANNER_TOOLS)
        self.router = router or ProviderRouter()
        # Retained as an optional compatibility parameter, but skills are
        # knowledge assets and are not used as a second tool registry.
        self.skills = skills

    async def plan(
        self, query: str, user_id: str, memory_context: list[dict[str, object]] | None = None
    ) -> IntentPlan:
        fallback = self.fallback_plan(query, user_id)
        if "fake_chat_provider" in self.router.degraded_modes:
            return fallback
        try:
            result = await self.router.chat(
                self._planner_prompt(query, user_id, memory_context or [])
            )
            if result.degraded or not isinstance(result.content, str):
                return fallback
            cleaned = (
                result.content.strip()
                .removeprefix("```json")
                .removeprefix("```")
                .removesuffix("```")
                .strip()
            )
            return self.validator.validate(IntentPlan.model_validate(json.loads(cleaned)))
        except (ProviderRecoverableError, ValueError, TypeError, json.JSONDecodeError):
            return fallback

    def fallback_plan(self, query: str, user_id: str) -> IntentPlan:
        return self.validator.validate(self._fallback_plan(query, user_id))

    def _planner_prompt(self, query: str, user_id: str, memories: list[dict[str, object]]) -> str:
        memory_values = [str(item.get("value", "")) for item in memories[:3]]
        return (
            "You are the AtlasHub enterprise knowledge-community planner. Select only registered tools and return JSON only. "
            'Schema: {"intent":"knowledge_qa|post_search|lost_found|post_draft|memory|eval|greeting",'
            '"tool_calls":[{"tool_name":"...","arguments":{}}],'
            '"confidence":0.0,"source":"model"}. '
            "Memories personalize planning but are never official evidence. "
            f"REGISTERED_TOOLS={json.dumps(sorted(self.validator.registered_tools), ensure_ascii=False)}\n"
            f"USER_ID={json.dumps(user_id, ensure_ascii=False)}\n"
            f"RELEVANT_MEMORIES={json.dumps(memory_values, ensure_ascii=False)}\n"
            f"USER_QUERY={json.dumps(query, ensure_ascii=False)}"
        )

    @staticmethod
    def _fallback_plan(query: str, user_id: str) -> IntentPlan:
        lowered = query.lower()
        if any(word in lowered for word in ["你好", "您好", "嗨", "hello", "hi"]):
            return IntentPlan(
                intent=Intent.GREETING, tool_calls=[], confidence=0.96, source="fallback"
            )
        if any(word in lowered for word in ["知识库", "制度", "流程", "规范", "产品文档", "接口", "api", "合同", "协议", "faq", "案例"]):
            return IntentPlan(
                intent=Intent.CAMPUS_QA,
                tool_calls=[ToolCall(tool_name="search_knowledge_base", arguments={"query": query})],
                confidence=0.94,
                source="fallback",
            )
        if any(word in lowered for word in ["起草", "发帖", "草稿", "写一篇", "帮我写"]):
            return IntentPlan(
                intent=Intent.POST_DRAFT,
                tool_calls=[ToolCall(tool_name="create_post_draft", arguments={"intent": query})],
                confidence=0.92,
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
                tool_calls=[
                    ToolCall(tool_name="load_user_memories", arguments={"user_id": user_id})
                ],
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
                ToolCall(tool_name="search_knowledge_base", arguments={"query": query}),
                ToolCall(tool_name="get_knowledge_service_info", arguments={"query": query}),
            ],
            confidence=0.84,
            source="fallback",
        )
