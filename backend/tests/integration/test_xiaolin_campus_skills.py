from __future__ import annotations

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
    evidence = venue_evidence({"query": "找东湖校区能坐200人的讲座场地，要投影"})
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
        ("东湖校区今天会下雨吗", "query_campus_weather"),
        ("我的导师是谁", "get_student_profile"),
    ],
)
def test_planner_routes_each_campus_intent_to_a_distinct_tool(query: str, tool: str) -> None:
    plan = StructuredPlanner().fallback_plan(query, "demo-user")

    assert [call.tool_name for call in plan.tool_calls] == [tool]


def test_complex_activity_plan_fans_out_to_multiple_tools() -> None:
    plan = StructuredPlanner().fallback_plan("帮我规划一场东湖校区200人讲座", "demo-user")

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


@pytest.mark.asyncio
async def test_weather_mcp_exposes_campus_weather_tool() -> None:
    tools = await mcp.list_tools()

    assert any(tool.name == "campus_weather" for tool in tools)


@pytest.mark.asyncio
async def test_venue_reservation_chat_returns_unpublished_confirmation_draft() -> None:
    response = await handle_chat(
        ChatRequest(
            session_id="venue-draft-session",
            user_id="demo-user",
            message="生成预约单：2026-06-04 14:00-17:00，东湖校区200人讲座场地",
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
