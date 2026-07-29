from __future__ import annotations

import json
import logging
from typing import Any

from app.xiaolin_agent.services.campus_tool_hub import CampusToolHub
from app.xiaolin_agent.services.llm_service import LLMService, MAIN_AGENT_MODEL
from app.xiaolin_agent.services.server_manager import ServerManager
from app.xiaolin_agent.services.student_profile_service import format_student_profile_for_prompt
from app.xiaolin_agent.skills import SkillRegistry

logger = logging.getLogger(__name__)


class ToolSelector:
    """Component that selects an API tool for every planned task."""

    TOOL_SELECTION_PROMPT = """你是浙江工商大学智能校园系统的工具选择器。你需要为每个任务选择最合适的工具。

<可用工具及其能力>
{tool_capabilities}
</可用工具及其能力>

任务计划：
{task_plan}

当前用户画像：
{student_profile}

请为每个任务选择最合适的工具，并以下格式返回工具选择方案：

{{
  "tool_selections": [
    {{
      "task_id": 1,
      "tool": "最适合处理此任务的工具名称",
      "params": {{"param1": "值1"}},
      "reason": "选择该工具的简短理由"
    }}
  ]
}}

规则：
1. 为每个任务选择一个最合适的API工具
2. 确保提供该工具所需的所有必要参数
3. 可以提供可选参数以提高结果准确性
4. 参数值应基于任务描述和用户请求提取
5. 如果必要参数在用户请求中不清楚，使用合理的默认值并在reason中说明
6. 如果任务非常一般，可以选择general_assistant工具
7. 如果任务依赖于其他任务的结果，可以使用占位符格式：{{TASK_X_RESULT}}，其中X是任务ID
"""

    @classmethod
    async def select_tools_for_tasks(cls, task_plan: dict[str, Any]) -> dict[str, Any]:
        logger.info("开始为任务计划选择工具")
        response_text = ""
        try:
            all_tools: list[Any] = []
            try:
                server_manager = await ServerManager.get_instance()
                all_tools = ServerManager.get_cached_tools()
                if not all_tools:
                    all_tools = await server_manager.list_all_tools()
            except Exception:
                logger.warning("MCP工具初始化失败，仅使用本地skill", exc_info=True)

            skill_tools = SkillRegistry.list_tools()
            all_tools = [*all_tools, *skill_tools]
            builtin_tools_description = await CampusToolHub.get_tool_info_for_planner()
            discovered_tools_description = "\n".join(tool.format_for_llm() for tool in all_tools)
            tools_description = "\n".join(
                item
                for item in [builtin_tools_description, discovered_tools_description]
                if item
            )
            prompt = cls.TOOL_SELECTION_PROMPT.format(
                tool_capabilities=tools_description,
                task_plan=json.dumps(task_plan, ensure_ascii=False, indent=2),
                student_profile=format_student_profile_for_prompt(),
            )
            llm = await LLMService.get_llm(model_name=MAIN_AGENT_MODEL, temperature=0.1)
            selection_response = await llm.ainvoke([{"role": "system", "content": prompt}])
            response_text = str(selection_response.content)
            json_match = response_text.strip()
            if "```json" in json_match:
                json_match = json_match.split("```json", 1)[1].split("```", 1)[0]
            tool_selections = json.loads(json_match)
            if not isinstance(tool_selections, dict):
                raise TypeError("工具选择必须是 JSON 对象")
            return tool_selections
        except json.JSONDecodeError:
            logger.error("工具选择 JSON 解析错误: %s", response_text, exc_info=True)
            return await cls._get_default_selections(task_plan)
        except Exception:
            logger.error("工具选择过程出错", exc_info=True)
            return await cls._get_default_selections(task_plan)

    @classmethod
    async def _get_default_selections(cls, task_plan: dict[str, Any]) -> dict[str, Any]:
        logger.warning("使用小林原版 general_assistant 默认工具")
        return {
            "tool_selections": [
                {
                    "task_id": task["id"],
                    "tool": "general_assistant",
                    "params": {
                        "query_type": "general",
                        "keywords": task["input"],
                    },
                    "reason": "Default selection due to error",
                }
                for task in task_plan.get("tasks", [])
            ]
        }
