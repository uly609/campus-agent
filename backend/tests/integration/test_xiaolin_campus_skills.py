from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.agent.planner.planner import StructuredPlanner
from app.agent.tools.campus_tools import CampusTools, build_registry
from app.campus_skills.adapters import (
    course_evidence,
    notice_evidence,
    profile_evidence,
    reservation_draft,
    venue_evidence,
)
from scripts.weather_mcp_server import mcp
from app.domain.schemas import ChatRequest
from app.services.chat_service import handle_chat
from app.services.xiaolin_service import stream_xiaolin_events
from app.services.repository import JsonRepository
from app.xiaolin_agent.ResponseGenerator import ResponseGenerator
from app.xiaolin_agent.services.chat_history_manager import ChatHistoryManager
from app.xiaolin_agent.services.llm_service import LLMService


class FakeXiaolinLLM:
    async def ainvoke(self, messages):
        prompt = "\n".join(str(item.get("content", "")) for item in messages)
        if "中央规划器" in prompt:
            return SimpleNamespace(
                content=json.dumps(
                    {
                        "tasks": [
                            {
                                "id": 1,
                                "task": "查询下沙校区讲座场地",
                                "input": "找下沙校区能坐200人的讲座场地，要投影",
                                "depends_on": [],
                            }
                        ]
                    },
                    ensure_ascii=False,
                )
            )
        if "工具选择器" in prompt:
            return SimpleNamespace(
                content=json.dumps(
                    {
                        "tool_selections": [
                            {
                                "task_id": 1,
                                "tool": "venue-booking",
                                "params": {
                                    "query": "找下沙校区能坐200人的讲座场地，要投影"
                                },
                                "reason": "使用小林场地 skill",
                            }
                        ]
                    },
                    ensure_ascii=False,
                )
            )
        return SimpleNamespace(content="下沙校区讲座场地")

    async def astream(self, messages):
        yield SimpleNamespace(content="下沙校区有符合条件的讲座场地，")
        yield SimpleNamespace(content="可继续确认日期和时段。")


def test_course_skill_uses_safe_demo_profile_to_filter_tuesday_schedule() -> None:
    evidence = course_evidence({"query": "查一下我周二的课表"})

    assert evidence
    assert any("数据结构与算法" in item.excerpt for item in evidence)
    assert all("周二" in item.excerpt for item in evidence)


def test_profile_skill_does_not_expose_sensitive_fields() -> None:
    excerpt = profile_evidence()[0].excerpt

    assert "计算机科学与技术" in excerpt
    assert "联系方式" not in excerpt
    assert "宿舍" not in excerpt
    assert "学号" not in excerpt


def test_venue_skill_filters_by_capacity_and_reservation_is_only_a_draft() -> None:
    evidence = venue_evidence({"query": "找下沙校区能坐200人的讲座场地，要投影"})
    draft = reservation_draft({"query": "生成预约单：2026-06-03下午200人讲座"})

    assert evidence
    assert all(item.metadata["raw"]["capacity"] >= 200 for item in evidence)
    assert all("存在冲突" not in item.excerpt for item in evidence)
    assert draft["requires_confirmation"] is True
    assert draft["published"] is False


def test_notice_skill_handles_natural_latest_scholarship_query() -> None:
    evidence = notice_evidence({"query": "查最新奖学金通知"})
    assert evidence
    assert any("奖学金" in item.title for item in evidence)


@pytest.mark.parametrize(
    ("query", "tool"),
    [
        ("我周二上什么课", "query_course_schedule"),
        ("查最新奖学金通知", "query_campus_notices"),
        ("找一个200人的报告厅", "query_campus_venues"),
        ("下沙校区今天会下雨吗", "query_campus_weather"),
        ("我的导师是谁", "get_student_profile"),
    ],
)
def test_planner_routes_each_campus_intent_to_a_distinct_tool(query: str, tool: str) -> None:
    plan = StructuredPlanner().fallback_plan(query, "demo-user")

    assert [call.tool_name for call in plan.tool_calls] == [tool]


def test_complex_activity_plan_fans_out_to_multiple_tools() -> None:
    plan = StructuredPlanner().fallback_plan("帮我规划一场下沙校区200人讲座", "demo-user")

    assert [call.tool_name for call in plan.tool_calls] == [
        "query_course_schedule",
        "query_campus_venues",
        "query_campus_weather",
        "query_campus_notices",
    ]


@pytest.mark.asyncio
async def test_copied_tools_are_registered_and_executable() -> None:
    registry = build_registry(CampusTools())

    result = await registry.call("query_course_schedule", {"query": "我的周二课表"})
    assert result.success is True
    assert result.data
    assert result.provenance[0]["synthetic_demo"] is True


@pytest.mark.asyncio
async def test_weather_mcp_exposes_campus_weather_tool() -> None:
    tools = await mcp.list_tools()

    assert any(tool.name == "campus_weather" for tool in tools)


@pytest.mark.asyncio
async def test_course_chat_exposes_planner_tool_and_judge_trace() -> None:
    response = await handle_chat(
        ChatRequest(
            session_id="xiaolin-trace-session",
            user_id="demo-user",
            message="查一下我周二的课表",
        )
    )

    plan = next(item for item in response.trace if item.get("event") == "intent_planned")
    tool = next(item for item in response.trace if item.get("event") == "tool_called")
    judge = next(item for item in response.trace if item.get("event") == "relevance_judged")
    assert plan["steps"][0]["tool"] == "query_course_schedule"
    assert tool["tool"] == "query_course_schedule"
    assert tool["success"] is True
    assert tool["result_count"] >= 1
    assert "latency_ms" in tool
    assert judge["evidence_count"] >= 1
    assert response.citations


@pytest.mark.asyncio
async def test_venue_reservation_chat_returns_unpublished_confirmation_draft() -> None:
    response = await handle_chat(
        ChatRequest(
            session_id="venue-draft-session",
            user_id="demo-user",
            message="生成预约单：2026-06-04 14:00-17:00，下沙校区200人讲座场地",
        )
    )

    assert "待审批的场地预约草稿" in response.answer.answer
    assert "尚未提交" in response.answer.answer
    assert response.citations == []
    assert any(
        item.get("event") == "tool_called"
        and item.get("tool") == "create_venue_reservation_draft"
        for item in response.trace
    )
    assert not any(item.get("event") == "replan" for item in response.trace)


@pytest.mark.asyncio
async def test_xiaolin_stream_emits_full_planner_tool_answer_flow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    async def fake_get_llm(cls, model_name="", stream=False, temperature=0.7):
        return FakeXiaolinLLM()

    monkeypatch.setattr(LLMService, "get_llm", classmethod(fake_get_llm))
    monkeypatch.setattr(ChatHistoryManager, "repo", JsonRepository(tmp_path))
    request = ChatRequest(
        session_id="xiaolin-stream-session",
        user_id="demo-user",
        message="找下沙校区能坐200人的讲座场地，要投影",
        is_agent=True,
    )
    events = [event async for event in stream_xiaolin_events(request)]

    assert any(event.get("subtype") == "task_plan" for event in events)
    assert any(event.get("subtype") == "tool_selections" for event in events)
    assert any(event.get("subtype") == "task_result" for event in events)
    selections = next(
        event["content"] for event in events if event.get("subtype") == "tool_selections"
    )
    assert selections[1]["tool"] == "venue-booking"
    answer = "".join(
        str(event.get("content", "")) for event in events if event.get("type") is None
    )
    assert "下沙校区" in answer
    history = await ChatHistoryManager.get_chat_history("xiaolin-stream-session")
    assert [item["role"] for item in history] == ["user", "assistant"]


@pytest.mark.asyncio
async def test_xiaolin_normal_mode_uses_original_simple_stream(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    async def fake_get_llm(cls, model_name="", stream=False, temperature=0.7):
        return FakeXiaolinLLM()

    monkeypatch.setattr(LLMService, "get_llm", classmethod(fake_get_llm))
    monkeypatch.setattr(ChatHistoryManager, "repo", JsonRepository(tmp_path))
    events = [
        event
        async for event in stream_xiaolin_events(
            ChatRequest(
                session_id="xiaolin-normal-session",
                user_id="demo-user",
                message="你好",
                is_agent=False,
            )
        )
    ]

    assert all(event.get("type") is None for event in events)
    assert "下沙校区" in "".join(str(event["content"]) for event in events)


@pytest.mark.asyncio
async def test_xiaolin_chat_images_are_analyzed_without_persisting_base64(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    model_messages: list[str] = []

    async def fake_analyze_chat_image(image_url: str) -> dict[str, object]:
        assert image_url.startswith("data:image/png;base64,")
        return {
            "summary": "绿色校园助手图标",
            "category": "图标",
            "color": "绿色",
            "_analysis": {
                "provider": "cloud_fallback",
                "model": "qwen-vl-plus",
                "degraded": False,
            },
        }

    async def fake_simple_response(cls, message: str, chat_history=None):
        model_messages.append(message)
        yield "图片里是绿色校园助手图标。"

    monkeypatch.setattr(
        "app.services.xiaolin_service.analyze_chat_image",
        fake_analyze_chat_image,
    )
    monkeypatch.setattr(
        ResponseGenerator,
        "create_simple_streaming_response",
        classmethod(fake_simple_response),
    )
    monkeypatch.setattr(ChatHistoryManager, "repo", JsonRepository(tmp_path))

    events = [
        event
        async for event in stream_xiaolin_events(
            ChatRequest(
                session_id="xiaolin-image-session",
                user_id="demo-user",
                message="这张图里有什么？",
                image_urls=["data:image/png;base64,dGVzdA=="],
            )
        )
    ]

    analysis = next(event for event in events if event.get("subtype") == "image_analysis")
    assert analysis["content"][0]["_analysis"]["model"] == "qwen-vl-plus"
    assert "绿色校园助手图标" in model_messages[0]
    history = await ChatHistoryManager.get_chat_history("xiaolin-image-session")
    assert "[已附带 1 张图片]" in history[0]["content"]
    assert "dGVzdA==" not in history[0]["content"]
