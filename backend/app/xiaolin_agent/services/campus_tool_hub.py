from __future__ import annotations

import json
import logging
from typing import Any, ClassVar

from app.xiaolin_agent.services.llm_service import LLMService, TOOL_LIBRARY_MODEL
from app.xiaolin_agent.services.student_profile_service import format_student_profile_for_prompt

logger = logging.getLogger(__name__)


class CampusToolHub:
    """XiaoLin's built-in campus tools, localized for Zhejiang Gongshang University."""

    _tool_info: ClassVar[str | None] = None

    @classmethod
    async def get_tool_info_for_planner(cls) -> str:
        if cls._tool_info is None:
            await cls._init_tool_info()
        return cls._tool_info or ""

    @classmethod
    async def _init_tool_info(cls) -> None:
        tools: list[dict[str, Any]] = [
            {
                "name": "general_assistant",
                "description": "通用大模型辅助工具。当任务没有专用 Skill 或 MCP Tool 可处理时，调用一次大模型，基于任务描述、用户输入、已有任务结果和学生画像生成辅助分析或回答。",
                "parameters": [
                    {"name": "query_type", "description": "查询类型，如 general、analysis、planning", "required": False},
                    {"name": "keywords", "description": "用户问题、任务输入或需要分析的关键词", "required": True},
                    {"name": "task", "description": "当前任务对象", "required": False},
                    {"name": "task_results", "description": "前置任务执行结果", "required": False},
                ],
            },
            {
                "name": "course_info",
                "description": "查询课程信息",
                "parameters": [
                    {"name": "course_id", "description": "课程ID", "required": False},
                    {"name": "course_name", "description": "课程名称", "required": False},
                    {"name": "teacher", "description": "教师姓名", "required": False},
                ],
            },
            {
                "name": "campus_map",
                "description": "查询校园地图和位置信息",
                "parameters": [
                    {"name": "location", "description": "位置名称", "required": True},
                    {"name": "detail", "description": "是否需要详细信息", "required": False},
                ],
            },
        ]
        formatted_tools = []
        for tool in tools:
            params_info = ", ".join(
                f"{param['name']}({'必需' if param.get('required', False) else '可选'})"
                for param in tool.get("parameters", [])
            )
            formatted_tools.append(
                f"工具名称: {tool['name']}\n描述: {tool['description']}\n参数: {params_info}\n"
            )
        cls._tool_info = "\n".join(formatted_tools)

    @classmethod
    async def call_api(cls, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        logger.info("调用小林内置工具: %s", tool_name)
        try:
            if tool_name == "general_assistant":
                return await cls._call_general_assistant(params)
            if tool_name == "course_info":
                return await cls._call_course_info(params)
            if tool_name == "campus_map":
                return await cls._call_campus_map(params)
            return {"error": f"未知的工具: {tool_name}"}
        except Exception as exc:
            logger.error("API调用出错: %s", exc, exc_info=True)
            return {"error": f"API调用出错: {exc}"}

    @classmethod
    async def _call_general_assistant(cls, params: dict[str, Any]) -> dict[str, Any]:
        query_type = params.get("query_type", "general")
        keywords = (
            params.get("keywords")
            or params.get("query")
            or params.get("input")
            or params.get("task_description")
            or ""
        )
        task = params.get("task") or {}
        task_results = params.get("task_results") or {}
        system_prompt = f"""你是浙江工商大学校园大脑中的通用大模型辅助工具。
你的职责是在没有专用 Tool / Skill 覆盖时，调用一次大模型辅助解决当前子任务。

要求：
1. 只回答当前子任务，不要编造工具没有返回的数据。
2. 如果需要外部系统数据但当前没有提供，请说明缺口并给出下一步建议。
3. 涉及校园事务时，优先结合学生画像和已有任务结果。
4. 输出应清晰、可执行，适合作为后续最终回复的中间结果。

当前用户画像：
{format_student_profile_for_prompt()}
"""
        user_prompt = f"""查询类型：{query_type}

当前任务：
{json.dumps(task, ensure_ascii=False, indent=2)}

用户输入 / 关键词：
{keywords}

已有任务结果：
{json.dumps(task_results, ensure_ascii=False, indent=2)}

请基于以上信息完成这一步任务。"""
        llm = await LLMService.get_llm(model_name=TOOL_LIBRARY_MODEL, temperature=0.2)
        response = await llm.ainvoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        return {
            "status": "success",
            "tool": "general_assistant",
            "query_type": query_type,
            "keywords": keywords,
            "result": response.content,
        }

    @classmethod
    async def _call_course_info(cls, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "courses": [
                {
                    "id": str(params.get("course_id") or "CS101"),
                    "name": str(params.get("course_name") or "计算机科学导论"),
                    "teacher": str(params.get("teacher") or "任课教师"),
                    "schedule": "周一 8:00-10:00",
                    "location": "下沙校区教学楼A-101",
                }
            ]
        }

    @classmethod
    async def _call_campus_map(cls, params: dict[str, Any]) -> dict[str, Any]:
        location = str(params.get("location", "下沙校区"))
        detail = bool(params.get("detail", False))
        basic_info: dict[str, Any] = {
            "name": location,
            "coordinates": "30.315, 120.389",
            "category": "校园地点",
        }
        if detail:
            basic_info.update(
                {
                    "description": f"{location}是浙江工商大学的校园区域。",
                    "facilities": ["电梯", "饮水机", "休息区"],
                    "opening_hours": "6:00-22:00",
                }
            )
        return basic_info
