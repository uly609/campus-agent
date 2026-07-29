from __future__ import annotations

import logging
import re
from typing import Any

from app.agent.tools.campus_tools import build_registry
from app.agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class TaskExecutor:
    """XiaoLin task executor with dependency placeholders and tool allowlisting."""

    @classmethod
    async def execute_task(
        cls,
        task: dict[str, Any],
        tool_selection: dict[str, Any],
        task_results: dict[int, Any],
        registry: ToolRegistry | None = None,
    ) -> Any:
        task_id = int(task.get("id", 0))
        tool_name = str(tool_selection.get("tool", ""))
        params = cls._resolve_params(dict(tool_selection.get("params", {})), task_results)
        params.setdefault("query", str(task.get("input", "")))
        active_registry = registry or build_registry()
        logger.info("XiaoLin executing task %s with %s", task_id, tool_name)
        try:
            result = await active_registry.call(tool_name, params)
        except Exception as exc:  # The executor converts tool faults into task-level errors.
            logger.exception("XiaoLin task %s failed", task_id)
            return {"error": str(exc), "task_id": task_id, "tool": tool_name}
        if not result.success:
            return {
                "error": result.error_message or result.error_code or "工具执行失败",
                "error_code": result.error_code,
                "task_id": task_id,
                "tool": tool_name,
                "latency_ms": result.latency_ms,
            }
        return {
            "tool": tool_name,
            "data": result.data,
            "provenance": result.provenance,
            "latency_ms": result.latency_ms,
        }

    @classmethod
    def _resolve_params(
        cls, params: dict[str, Any], task_results: dict[int, Any]
    ) -> dict[str, Any]:
        for key, value in list(params.items()):
            if isinstance(value, str):
                for placeholder in re.findall(r"\{TASK_\d+_RESULT(?:\.\w+)*\}", value):
                    value = value.replace(placeholder, str(cls.resolve_placeholder(placeholder, task_results)))
                params[key] = value
            elif isinstance(value, dict):
                params[key] = cls._resolve_params(value, task_results)
        return params

    @staticmethod
    def resolve_placeholder(placeholder: str, task_results: dict[int, Any]) -> Any:
        if not placeholder.startswith("{TASK_") or not placeholder.endswith("}"):
            return placeholder
        try:
            parts = placeholder[1:-1].split(".")
            task_id = int(parts[0].split("_")[1])
            if task_id not in task_results or task_results[task_id].get("status") != "success":
                return f"{{TASK_{task_id}_RESULT_NOT_FOUND}}"
            value: Any = task_results[task_id]["api_result"]
            for key in parts[1:]:
                if isinstance(value, dict):
                    value = value.get(key, f"{{KEY_{key}_NOT_FOUND}}")
                else:
                    return "{INVALID_KEY_PATH}"
            return value
        except (KeyError, TypeError, ValueError) as exc:
            return f"{{PLACEHOLDER_ERROR: {exc}}}"
