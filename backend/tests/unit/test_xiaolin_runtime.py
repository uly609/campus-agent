from __future__ import annotations

import pytest

from app.xiaolin_agent.ResponseGenerator import ResponseGenerator
from app.xiaolin_agent.TaskExecutor import TaskExecutor
from app.xiaolin_agent.services.llm_service import LLMService
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


def test_normal_mode_refuses_to_invent_unretrieved_campus_facts() -> None:
    prompt = ResponseGenerator._create_simple_response_prompt()

    assert "普通模式没有调用校园知识库" in prompt
    assert "不得凭模型记忆" in prompt
    assert "不代表已连接真实学籍或教务系统" in prompt


@pytest.mark.asyncio
async def test_normal_mode_blocks_campus_fact_generation_before_calling_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_get_llm(cls, model_name="", stream=False, temperature=0.7):
        raise AssertionError("campus fact query must not call the model in normal mode")

    monkeypatch.setattr(LLMService, "get_llm", classmethod(fail_get_llm))
    chunks = [
        chunk
        async for chunk in ResponseGenerator.create_simple_streaming_response(
            "学校图书馆在哪",
        )
    ]

    assert "普通模式没有检索校园资料" in "".join(chunks)
    assert "请开启 Agent" in "".join(chunks)


def test_agent_mode_requires_demo_and_verified_source_disclosure() -> None:
    prompt = ResponseGenerator._create_response_prompt(
        {
            "user_input": "我的课表",
            "task_planning": {},
            "tool_selection": {},
            "task_execution": {},
        }
    )

    assert "只能称为“演示数据”" in prompt
    assert "data_mode: verified_official" in prompt
