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

    _TOOL_ALIASES = {
        "campus_knowledge": "search_campus_docs",
        "community_search": "search_posts",
        "post_creation": "create_post_draft",
        "memory_management": "load_user_memories",
        "evaluation": "get_eval_report",
        "course_schedule": "query_course_schedule",
        "campus_notice": "query_campus_notices",
        "venue_coordination": "query_campus_venues",
        "student_profile": "get_student_profile",
        # XiaoLin always enters campus facts through the local-first retrieval policy.
        "search_official_web": "search_campus_docs",
    }

    @classmethod
    async def execute_task(
        cls,
        task: dict[str, Any],
        tool_selection: dict[str, Any],
        task_results: dict[int, Any],
    ) -> Any:
        task_id = int(task.get("id", 0))
        selected_tool_name = str(tool_selection.get("tool", "unknown_tool"))
        tool_name = cls._TOOL_ALIASES.get(selected_tool_name, selected_tool_name)
        logger.info("开始执行任务 %s，使用工具 %s", task_id, tool_name)
        try:
            params = dict(tool_selection.get("params", {}))
            nested_params = params.pop("params", None)
            if isinstance(nested_params, dict):
                params = {**params, **nested_params}
            if tool_name == "create_post_draft" and "intent" not in params:
                params["intent"] = params.get("query") or task.get("input") or task.get("task") or ""
            if tool_name == "campus_weather":
                params = cls._normalize_weather_params(task, params)
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
                    cached_tools = ServerManager.get_cached_tools()
                    if any(
                        tool.name == tool_name and tool.server_name == server_name
                        for tool in cached_tools
                    ):
                        try:
                            result = await server.execute_tool(tool_name, params)
                            if not (isinstance(result, dict) and "error" in result):
                                return result
                            if tool_name == "campus_weather":
                                return await cls._weather_fallback(task, params, result)
                            return result
                        except Exception as exc:
                            logger.error(
                                "Error executing tool %s on server %s: %s",
                                tool_name,
                                server_name,
                                exc,
                            )
                            if tool_name == "campus_weather":
                                return await cls._weather_fallback(
                                    task,
                                    params,
                                    {"error": exc.__class__.__name__},
                                )
                            return {"error": str(exc)}
                except Exception:
                    logger.error("Error listing tools from server %s", server_name, exc_info=True)

            api_result = await CampusToolHub.call_api(tool_name, params)
            if "error" not in api_result:
                return api_result
            return {
                "error": f"No server found with tool: {tool_name}",
                "tool": selected_tool_name,
            }
        except Exception as exc:
            logger.error("任务 %s 执行错误: %s", task_id, exc, exc_info=True)
            return {
                "error": f"执行任务时出错: {exc}",
                "task_id": task_id,
                "tool": tool_name,
            }

    @classmethod
    async def _weather_fallback(
        cls,
        task: dict[str, Any],
        params: dict[str, Any],
        mcp_error: dict[str, Any],
    ) -> Any:
        from app.agent.tools.campus_tools import build_registry

        query = str(
            params.get("query")
            or params.get("location")
            or task.get("input")
            or task.get("task")
            or "杭州天气"
        )
        fallback = await build_registry().call("query_campus_weather", {"query": query})
        if not fallback.success:
            return mcp_error
        data = fallback.data
        if isinstance(data, list):
            for item in data:
                metadata = item.setdefault("metadata", {})
                metadata["mcp_degraded"] = True
                metadata["mcp_server"] = "campusflow-weather"
        return data

    @staticmethod
    def _normalize_weather_params(
        task: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        query = " ".join(
            str(value)
            for value in (
                params.get("query"),
                params.get("location"),
                task.get("input"),
                task.get("task"),
            )
            if value
        )
        location = next(
            (
                candidate
                for candidate in ("下沙校区", "教工路校区", "浙江工商大学", "杭州")
                if candidate in query
            ),
            str(params.get("location") or "杭州").strip(),
        )
        days_value = params.get("days", 2 if "明天" in query else 1)
        try:
            days = max(1, min(int(days_value), 7))
        except (TypeError, ValueError):
            days = 1
        if "明天" in query or "明日" in query:
            days = max(days, 2)
        return {"location": location, "days": days}

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
