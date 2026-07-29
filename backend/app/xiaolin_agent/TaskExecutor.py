from __future__ import annotations

import logging
import re
from typing import Any

from app.xiaolin_agent.services.campus_tool_hub import CampusToolHub
from app.xiaolin_agent.services.server_manager import ServerManager
from app.xiaolin_agent.skills import SkillRegistry

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Execute a task using the tool selected by XiaoLin."""

    @classmethod
    async def execute_task(
        cls,
        task: dict[str, Any],
        tool_selection: dict[str, Any],
        task_results: dict[int, Any],
    ) -> Any:
        task_id = int(task.get("id", 0))
        tool_name = str(tool_selection.get("tool", "unknown_tool"))
        logger.info("开始执行任务 %s，使用工具 %s", task_id, tool_name)
        try:
            params = dict(tool_selection.get("params", {}))
            for param_key, param_value in params.items():
                if isinstance(param_value, str) and "{" in param_value:
                    placeholders = re.findall(r"\{TASK_\d+_RESULT(?:\.\w+)*\}", param_value)
                    for placeholder in placeholders:
                        resolved = cls.resolve_placeholder(placeholder, task_results)
                        params[param_key] = param_value.replace(placeholder, str(resolved))

            if SkillRegistry.has_tool(tool_name):
                return await SkillRegistry.execute_tool(tool_name, params)

            if tool_name == "general_assistant":
                params.setdefault("keywords", task.get("input") or task.get("task") or "")
                params.setdefault("task", task)
                params.setdefault("task_results", task_results)
                return await CampusToolHub.call_api(tool_name, params)

            for server_name, server in ServerManager._servers.items():
                try:
                    tools = await server.list_tools()
                    if any(tool.name == tool_name for tool in tools):
                        try:
                            return await server.execute_tool(tool_name, params)
                        except Exception as exc:
                            logger.error(
                                "Error executing tool %s on server %s: %s",
                                tool_name,
                                server_name,
                                exc,
                            )
                            return {"error": str(exc)}
                except Exception:
                    logger.error("Error listing tools from server %s", server_name, exc_info=True)

            api_result = await CampusToolHub.call_api(tool_name, params)
            if "error" not in api_result:
                return api_result
            return f"No server found with tool: {tool_name}"
        except Exception as exc:
            logger.error("任务 %s 执行错误: %s", task_id, exc, exc_info=True)
            return {
                "error": f"执行任务时出错: {exc}",
                "task_id": task_id,
                "tool": tool_name,
            }

    @classmethod
    def resolve_placeholder(cls, placeholder: str, task_results: dict[int, Any]) -> Any:
        if not placeholder.startswith("{TASK_") or not placeholder.endswith("}"):
            return placeholder
        try:
            parts = placeholder[1:-1].split(".")
            task_id = int(parts[0].split("_")[1])
            key_path = parts[1:]
            if task_id not in task_results or task_results[task_id].get("status") != "success":
                return f"{{TASK_{task_id}_RESULT_NOT_FOUND}}"
            value = task_results[task_id]["api_result"]
            for key in key_path:
                if isinstance(value, dict):
                    value = value.get(key, f"{{KEY_{key}_NOT_FOUND}}")
                else:
                    return "{INVALID_KEY_PATH}"
            return value
        except Exception as exc:
            return f"{{PLACEHOLDER_ERROR: {exc}}}"
