from __future__ import annotations

import json
import logging
from typing import Any

from app.agent.planner.planner import StructuredPlanner
from app.llm.base import ProviderRecoverableError
from app.llm.router import ProviderRouter

logger = logging.getLogger(__name__)


class TaskPlanner:
    """XiaoLin central planner adapted to CampusFlow's routed providers."""

    PLANNING_PROMPT = """你是浙江工商大学智能校园系统的中央规划器。
请分析用户请求，将其分解为有依赖关系、可执行的子任务，只返回 JSON：
{{"tasks":[{{"id":1,"task":"具体任务描述","input":"任务输入","depends_on":[]}}],"final_output_task_id":1}}

规则：
1. 每个任务必须精确且可由一个校园工具完成；
2. 复杂请求拆分为多个任务，简单请求只生成一个任务；
3. 后续任务依赖前置结果时，在 depends_on 中填写前置任务 id；
4. 最多生成 6 个任务，不得输出 JSON 之外的内容。

用户请求：{user_request}
相关长期记忆（只能个性化，不是官方证据）：{memory_context}
"""

    @classmethod
    async def create_task_plan(
        cls,
        user_request: str,
        user_id: str = "demo-user",
        memory_context: list[dict[str, object]] | None = None,
    ) -> dict[str, Any]:
        router = ProviderRouter()
        if "fake_chat_provider" not in router.degraded_modes:
            try:
                result = await router.chat(
                    cls.PLANNING_PROMPT.format(
                        user_request=user_request,
                        memory_context=json.dumps(memory_context or [], ensure_ascii=False),
                    )
                )
                if isinstance(result.content, str) and not result.degraded:
                    plan = cls._parse_plan(result.content)
                    if plan["tasks"]:
                        return plan
            except (ProviderRecoverableError, ValueError, TypeError, json.JSONDecodeError):
                logger.warning("XiaoLin model planning failed; using validated fallback", exc_info=True)
        return cls._fallback_plan(user_request, user_id)

    @staticmethod
    def _parse_plan(content: str) -> dict[str, Any]:
        cleaned = (
            content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        )
        raw = json.loads(cleaned)
        tasks = raw.get("tasks", [])
        if not isinstance(tasks, list) or len(tasks) > 6:
            raise ValueError("invalid XiaoLin task count")
        normalized: list[dict[str, Any]] = []
        known_ids: set[int] = set()
        for index, item in enumerate(tasks, start=1):
            if not isinstance(item, dict):
                raise ValueError("invalid XiaoLin task")
            task_id = int(item.get("id", index))
            depends_on = [int(value) for value in item.get("depends_on", [])]
            if any(dep not in known_ids for dep in depends_on):
                raise ValueError("task dependency must reference an earlier task")
            normalized.append(
                {
                    "id": task_id,
                    "task": str(item.get("task", "处理校园请求"))[:200],
                    "input": str(item.get("input", ""))[:500],
                    "depends_on": depends_on,
                }
            )
            known_ids.add(task_id)
        return {
            "tasks": normalized,
            "final_output_task_id": int(raw.get("final_output_task_id", normalized[-1]["id"])),
        }

    @staticmethod
    def _fallback_plan(user_request: str, user_id: str) -> dict[str, Any]:
        intent_plan = StructuredPlanner().fallback_plan(user_request, user_id)
        tasks: list[dict[str, Any]] = []
        tool_hints: dict[int, dict[str, Any]] = {}
        for index, call in enumerate(intent_plan.tool_calls, start=1):
            tasks.append(
                {
                    "id": index,
                    "task": TaskPlanner._task_description(call.tool_name),
                    "input": user_request,
                    "depends_on": [],
                }
            )
            tool_hints[index] = {"tool": call.tool_name, "params": dict(call.arguments)}
        if not tasks:
            tasks = [{"id": 1, "task": "直接回答用户", "input": user_request, "depends_on": []}]
            tool_hints[1] = {"tool": "general_assistant", "params": {"query": user_request}}
        return {
            "tasks": tasks,
            "final_output_task_id": tasks[-1]["id"],
            "tool_hints": tool_hints,
            "intent": intent_plan.intent.value,
            "source": "validated_fallback",
        }

    @staticmethod
    def _task_description(tool_name: str) -> str:
        labels = {
            "search_campus_docs": "检索校园官方知识",
            "search_posts": "检索校园社区帖子",
            "search_lost_and_found": "查找失物招领线索",
            "get_campus_service_info": "查询校园服务信息",
            "create_post_draft": "生成校园帖子草稿",
            "load_user_memories": "召回相关长期记忆",
            "get_eval_report": "读取 Agent 评测报告",
            "query_course_schedule": "查询个人课表",
            "query_campus_notices": "查询校园通知",
            "query_campus_venues": "筛选校园场地",
            "query_campus_weather": "查询校园天气",
            "get_student_profile": "读取隐私安全的学生画像",
            "create_venue_reservation_draft": "生成场地预约草稿",
        }
        return labels.get(tool_name, "处理用户请求")
