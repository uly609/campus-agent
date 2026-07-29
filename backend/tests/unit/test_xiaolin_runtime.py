from __future__ import annotations

import pytest

from app.xiaolin_agent.TaskExecutor import TaskExecutor
from app.xiaolin_agent.services.server_manager import ServerManager
from app.xiaolin_agent.services.student_profile_service import (
    format_student_profile_for_prompt,
)


@pytest.mark.asyncio
async def test_server_manager_exposes_executable_tools_instead_of_skill_groups() -> None:
    manager = await ServerManager.get_instance()
    names = {tool.name for tool in await manager.list_all_tools()}

    assert "search_campus_docs" in names
    assert "query_campus_venues" in names
    assert "campus_knowledge" not in names
    assert "venue_coordination" not in names


@pytest.mark.asyncio
async def test_task_executor_accepts_legacy_skill_group_aliases() -> None:
    await ServerManager.get_instance()

    result = await TaskExecutor.execute_task(
        {"id": 1, "task": "查询下沙校区讲座场地", "input": "下沙校区讲座场地"},
        {
            "tool": "venue_coordination",
            "params": {"query": "下沙校区讲座场地", "params": {"campus": "下沙"}},
        },
        {},
    )

    assert isinstance(result, list)
    assert result
    assert all("下沙" in item["metadata"]["raw"]["campus"] for item in result)


def test_xiaolin_chat_profile_excludes_personal_identity_fields() -> None:
    prompt = format_student_profile_for_prompt()

    assert "王浩蒙" not in prompt
    assert "学号" in prompt
    assert "不要猜测或称呼用户姓名" in prompt
