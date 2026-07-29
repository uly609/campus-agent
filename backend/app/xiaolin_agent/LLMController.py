from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.agent.tools.campus_tools import build_registry
from app.xiaolin_agent.TaskExecutor import TaskExecutor
from app.xiaolin_agent.TaskPlanner import TaskPlanner
from app.xiaolin_agent.ToolSelector import ToolSelector

logger = logging.getLogger(__name__)


async def get_process_info(
    message: str,
    user_id: str = "demo-user",
    memory_context: list[dict[str, object]] | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Run XiaoLin's planner-selector-executor pipeline and emit its original event protocol."""
    yield {"type": "step", "content": "任务规划中..."}
    task_plan = await TaskPlanner.create_task_plan(message, user_id, memory_context)
    tasks = task_plan.get("tasks", [])
    yield {"type": "data", "subtype": "task_plan", "content": tasks}

    yield {"type": "step", "content": "工具选择中..."}
    tool_selections = await ToolSelector.select_tools_for_tasks(task_plan)
    task_to_tool = {
        int(selection["task_id"]): selection
        for selection in tool_selections.get("tool_selections", [])
    }
    yield {"type": "data", "subtype": "tool_selections", "content": task_to_tool}

    task_results: dict[int, dict[str, Any]] = {}
    registry = build_registry()
    for task in tasks:
        task_id = int(task["id"])
        yield {"type": "step", "content": f"执行任务：{task['task']}..."}
        dependencies = [int(value) for value in task.get("depends_on", [])]
        dependencies_met = all(
            task_results.get(dep, {}).get("status") == "success" for dep in dependencies
        )
        if not dependencies_met:
            task_results[task_id] = {"status": "skipped", "reason": "依赖任务失败"}
        else:
            selection = task_to_tool.get(task_id)
            if selection is None:
                task_results[task_id] = {"status": "error", "error": "没有可执行的工具"}
            else:
                result = await TaskExecutor.execute_task(
                    task, selection, task_results, registry=registry
                )
                if isinstance(result, dict) and "error" in result:
                    task_results[task_id] = {
                        "status": "error",
                        "error": result["error"],
                        "tool": selection["tool"],
                    }
                else:
                    task_results[task_id] = {
                        "status": "success",
                        "api_result": result,
                    }
        yield {
            "type": "data",
            "subtype": "task_result",
            "content": {"task_id": task_id, "result": task_results[task_id]},
        }

    process_info = {
        "user_input": message,
        "steps": ["任务规划完成", "工具选择完成", "任务执行完成"],
        "task_planning": task_plan,
        "tool_selection": tool_selections,
        "task_execution": task_results,
    }
    logger.info("XiaoLin completed %s task(s)", len(tasks))
    yield {"type": "data", "subtype": "process_summary", "content": process_info}
