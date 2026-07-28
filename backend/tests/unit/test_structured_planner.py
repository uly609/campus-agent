from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agent.planner import (
    IntentPlan,
    PlanValidationError,
    PlanValidator,
    StructuredPlanner,
    ToolCall,
)
from app.domain.enums import Intent


@pytest.mark.asyncio
async def test_post_search_plan_is_typed_and_executable() -> None:
    plan = await StructuredPlanner().plan("帮我搜索二手帖子", "u1")

    assert plan.intent == Intent.POST_SEARCH
    assert plan.tool_calls == [
        ToolCall(tool_name="search_posts", arguments={"query": "帮我搜索二手帖子"})
    ]
    assert plan.to_steps() == [{"tool": "search_posts", "args": {"query": "帮我搜索二手帖子"}}]


def test_plan_rejects_unregistered_tool_before_execution() -> None:
    plan = IntentPlan(
        intent=Intent.POST_SEARCH,
        tool_calls=[ToolCall(tool_name="unknown_tool", arguments={"query": "二手"})],
        confidence=0.8,
    )

    with pytest.raises(PlanValidationError, match="not registered"):
        PlanValidator({"search_posts"}).validate(plan)


def test_plan_rejects_missing_required_arguments() -> None:
    plan = IntentPlan(
        intent=Intent.POST_SEARCH,
        tool_calls=[ToolCall(tool_name="search_posts", arguments={})],
        confidence=0.8,
    )

    with pytest.raises(PlanValidationError, match="missing required arguments: query"):
        PlanValidator({"search_posts"}).validate(plan)


def test_plan_schema_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        IntentPlan(intent=Intent.GREETING, tool_calls=[], confidence=1.1)


def test_plan_rejects_invalid_argument_type_before_execution() -> None:
    plan = IntentPlan(
        intent=Intent.POST_SEARCH,
        tool_calls=[ToolCall(tool_name="search_posts", arguments={"query": 123})],
        confidence=0.8,
    )

    with pytest.raises(PlanValidationError, match="must be str"):
        PlanValidator({"search_posts"}).validate(plan)


class ModelPlannerRouter:
    degraded_modes: list[str] = []

    async def chat(self, prompt: str):
        from app.llm.base import ProviderResult

        assert "SKILL_CATALOG" in prompt
        assert "住在西区" in prompt
        return ProviderResult(
            role="chat",
            provider="test",
            model="planner",
            content=(
                '{"intent":"post_search","tool_calls":['
                '{"tool_name":"search_posts","arguments":{"query":"篮球搭子"}}],'
                '"confidence":0.93,"source":"model"}'
            ),
            degraded=False,
            latency_ms=1,
        )


@pytest.mark.asyncio
async def test_model_planner_selects_registered_tool_from_skill_catalog() -> None:
    planner = StructuredPlanner(router=ModelPlannerRouter())
    plan = await planner.plan("找篮球搭子", "u1", [{"value": "我住在西区", "memory_type": "fact"}])

    assert plan.source == "model"
    assert plan.tool_calls[0].tool_name == "search_posts"
