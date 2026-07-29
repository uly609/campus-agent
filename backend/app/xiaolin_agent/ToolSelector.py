from __future__ import annotations

import json
import logging
from typing import Any

from app.agent.skills.registry import default_skill_registry
from app.agent.tools.campus_tools import build_registry
from app.llm.base import ProviderRecoverableError
from app.llm.router import ProviderRouter

logger = logging.getLogger(__name__)


class ToolSelector:
    """XiaoLin per-task tool selector backed by CampusFlow's allowlisted registry."""

    TOOL_SELECTION_PROMPT = """你是浙江工商大学智能校园系统的工具选择器。
请为任务计划中的每个任务选择一个最合适的工具，只返回 JSON：
{{"tool_selections":[{{"task_id":1,"tool":"工具名","params":{{}},"reason":"选择理由"}}]}}

可用工具：{tool_capabilities}
任务计划：{task_plan}
规则：只能使用可用工具；参数来自任务输入；依赖结果可写成 {{TASK_1_RESULT.key}}。
"""

    @classmethod
    async def select_tools_for_tasks(cls, task_plan: dict[str, Any]) -> dict[str, Any]:
        registry = build_registry()
        allowed = registry.tool_names
        router = ProviderRouter()
        if "fake_chat_provider" not in router.degraded_modes:
            try:
                catalog = default_skill_registry().planner_catalog()
                result = await router.chat(
                    cls.TOOL_SELECTION_PROMPT.format(
                        tool_capabilities=json.dumps(catalog, ensure_ascii=False),
                        task_plan=json.dumps(
                            {"tasks": task_plan.get("tasks", [])}, ensure_ascii=False
                        ),
                    )
                )
                if isinstance(result.content, str) and not result.degraded:
                    selections = cls._parse_selections(result.content, task_plan, allowed)
                    if selections["tool_selections"]:
                        return selections
            except (ProviderRecoverableError, ValueError, TypeError, json.JSONDecodeError):
                logger.warning("XiaoLin model tool selection failed; using planner hints", exc_info=True)
        return cls._get_default_selections(task_plan, allowed)

    @staticmethod
    def _parse_selections(
        content: str, task_plan: dict[str, Any], allowed: frozenset[str]
    ) -> dict[str, Any]:
        cleaned = (
            content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        )
        raw = json.loads(cleaned)
        task_ids = {int(task["id"]) for task in task_plan.get("tasks", [])}
        selections = []
        for item in raw.get("tool_selections", []):
            task_id = int(item["task_id"])
            tool = str(item["tool"])
            if task_id not in task_ids or tool not in allowed:
                raise ValueError("unknown task or tool")
            params = item.get("params", {})
            if not isinstance(params, dict):
                raise ValueError("tool params must be an object")
            selections.append(
                {
                    "task_id": task_id,
                    "tool": tool,
                    "params": params,
                    "reason": str(item.get("reason", "模型根据任务选择"))[:200],
                }
            )
        return {"tool_selections": selections, "source": "model"}

    @staticmethod
    def _get_default_selections(
        task_plan: dict[str, Any], allowed: frozenset[str]
    ) -> dict[str, Any]:
        hints = task_plan.get("tool_hints", {})
        selections: list[dict[str, Any]] = []
        for task in task_plan.get("tasks", []):
            task_id = int(task["id"])
            hint = hints.get(task_id) or hints.get(str(task_id)) or {}
            tool = str(hint.get("tool", "search_campus_docs"))
            if tool == "general_assistant" or tool not in allowed:
                tool = "search_campus_docs"
            params = dict(hint.get("params", {}))
            params.setdefault("query", str(task.get("input", "")))
            selections.append(
                {
                    "task_id": task_id,
                    "tool": tool,
                    "params": params,
                    "reason": "使用经过白名单校验的 Planner 建议",
                }
            )
        return {"tool_selections": selections, "source": "validated_fallback"}
