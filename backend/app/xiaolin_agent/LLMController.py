from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

import pydantic

from app.xiaolin_agent.TaskExecutor import TaskExecutor
from app.xiaolin_agent.TaskPlanner import TaskPlanner
from app.xiaolin_agent.ToolSelector import ToolSelector

logger = logging.getLogger(__name__)


async def get_process_info(message: str) -> AsyncGenerator[dict[str, Any], None]:
    yield {"type": "step", "content": "任务规划中..."}
    task_plan = await TaskPlanner.create_task_plan(message)
    tasks = task_plan.get("tasks", [])
    yield {"type": "data", "subtype": "task_plan", "content": tasks}

    yield {"type": "step", "content": "工具选择中..."}
    tool_selections = await ToolSelector.select_tools_for_tasks(task_plan)
    task_to_tool_map = {
        selection["task_id"]: selection
        for selection in tool_selections.get("tool_selections", [])
    }
    yield {"type": "data", "subtype": "tool_selections", "content": task_to_tool_map}

    task_results: dict[int, dict[str, Any]] = {}
    for task in tasks:
        yield {"type": "step", "content": f"执行任务: {task['task']}..."}
        task_id = int(task.get("id", 0))
        dependencies = [int(value) for value in task.get("depends_on", [])]
        dependencies_met = all(
            dependency in task_results
            and task_results[dependency].get("status") == "success"
            for dependency in dependencies
        )
        if not dependencies_met:
            task_results[task_id] = {"status": "skipped", "reason": "依赖任务失败"}
            continue

        tool_selection = task_to_tool_map.get(
            task_id,
            {
                "tool": "general_assistant",
                "params": {
                    "query_type": "general",
                    "keywords": task.get("input", ""),
                },
            },
        )
        result = await TaskExecutor.execute_task(task, tool_selection, task_results)
        if isinstance(result, dict) and "error" in result:
            task_results[task_id] = {"status": "error", "error": result["error"]}
            yield {
                "type": "data",
                "subtype": "task_result",
                "content": {"task_id": task_id, "result": result},
            }
        else:
            if isinstance(result, pydantic.BaseModel):
                api_result = result.model_dump()
            else:
                api_result = result
            task_results[task_id] = {"status": "success", "api_result": api_result}
            yield {
                "type": "data",
                "subtype": "task_result",
                "content": {"task_id": task_id, "result": result},
            }

    process_info = {
        "user_input": message,
        "task_planning": task_plan,
        "tool_selection": tool_selections,
        "task_execution": task_results,
    }
    logger.debug("Process info: %s", json.dumps(process_info, ensure_ascii=False, default=str))
    yield {"type": "data", "subtype": "process_summary", "content": process_info}
