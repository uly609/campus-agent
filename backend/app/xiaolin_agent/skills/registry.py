from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, ClassVar

from app.agent.tools.campus_tools import build_registry

SkillHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]] | dict[str, Any]]


@dataclass
class SkillRecord:
    name: str
    description: str
    handler: SkillHandler

    def format_for_llm(self) -> str:
        return f"""
Tool: {self.name}
Description: {self.description}
Arguments:
- query: 用户原始查询或任务描述。可选。
- params: 从用户请求中提取的结构化参数。可选。
"""


async def _call_registry(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
    result = await build_registry().call(tool_name, params)
    if not result.success:
        return {"error": result.error_message or result.error_code or "工具执行失败"}
    data = result.data
    if isinstance(data, dict):
        return data
    return {"status": "success", "data": data}


async def _query_schedule(params: dict[str, Any]) -> dict[str, Any]:
    return await _call_registry("query_course_schedule", params)


async def _query_notices(params: dict[str, Any]) -> dict[str, Any]:
    return await _call_registry("query_campus_notices", params)


async def _query_or_reserve_venue(params: dict[str, Any]) -> dict[str, Any]:
    action = str(params.get("action", "query")).lower()
    tool = "create_venue_reservation_draft" if action in {"reserve", "book", "预约"} else "query_campus_venues"
    return await _call_registry(tool, params)


class SkillRegistry:
    """The original XiaoLin local-skill boundary, backed by Zhejiang Gongshang data."""

    _skills: ClassVar[dict[str, SkillRecord]] = {
        "course-schedule": SkillRecord("course-schedule", "查询演示课表；未连接真实教务系统", _query_schedule),
        "campus-notice": SkillRecord("campus-notice", "查询演示校园通知；不是学校实时通知", _query_notices),
        "venue-booking": SkillRecord("venue-booking", "查询演示场地或生成不会提交的预约草稿", _query_or_reserve_venue),
    }
    _aliases: ClassVar[dict[str, str]] = {
        "course_schedule": "course-schedule",
        "course_scheduler": "course-schedule",
        "schedule_query": "course-schedule",
        "课表查询": "course-schedule",
        "campus_notice": "campus-notice",
        "campus_notices": "campus-notice",
        "notice_query": "campus-notice",
        "校园通知": "campus-notice",
        "venue_booking": "venue-booking",
        "venue_query": "venue-booking",
        "campus_venue": "venue-booking",
        "场地查询": "venue-booking",
        "场地预约": "venue-booking",
    }

    @classmethod
    def list_tools(cls) -> list[SkillRecord]:
        return list(cls._skills.values())

    @classmethod
    def get_tool(cls, name: str) -> SkillRecord | None:
        return cls._skills.get(cls._aliases.get(name, name))

    @classmethod
    def has_tool(cls, name: str) -> bool:
        return cls.get_tool(name) is not None

    @classmethod
    async def execute_tool(cls, name: str, params: dict[str, Any]) -> dict[str, Any]:
        skill = cls.get_tool(name)
        if skill is None:
            return {"error": f"未知 skill: {name}", "tool": name}
        result = skill.handler(params or {})
        if inspect.isawaitable(result):
            result = await result
        return result
