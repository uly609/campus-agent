from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.campus_skills.services.student_profile_service import format_student_profile_for_prompt
from app.llm.router import ProviderRouter
from app.security.pii import redact_pii

logger = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: object) -> object:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


class ResponseGenerator:
    """生成最终用户响应的类 - adapted from XiaoLin's FastAPI implementation."""

    @classmethod
    def _student_profile_prompt(cls) -> str:
        return format_student_profile_for_prompt()

    @classmethod
    def _create_response_prompt(cls, process_info: dict[str, Any]) -> str:
        return f"""你是浙江工商大学智能校园助手「浙商小林」。你的回答要自然、亲切、简洁，像一位靠谱的校园服务同学在和用户聊天。

回答风格：
1. 先直接回应用户的问题，不要绕到“我准备如何处理”。
2. 简单寒暄、问候、闲聊时，用1-2句轻松回应即可，不要自我介绍过长。
3. 涉及校园事务时保持准确、清楚、友好；信息不足时自然说明，并给出可行建议。
4. 可以少量使用emoji，但不要连续堆叠，不要显得刻意卖萌。
5. 除非用户明确要求，否则不要暴露任务规划、工具选择、工具名称、服务器状态、调用失败、内部错误等处理过程。
6. 如果工具结果为空、失败或不可用，请基于已有信息给出自然回复；无法确定时说“我这边暂时没有查到准确信息”，不要提“工具/服务器/MCP/任务失败”。
7. 不要重复用户原话来凑字数，不要说“刚才我收到了你的问候”这类流程化表达。

以下是当前用户的学生画像，只供你理解用户背景和提供个性化校园服务，不要主动完整展示：
{cls._student_profile_prompt()}

以下过程信息只供你理解上下文，不要原样展示给用户：
**过程信息：**
用户输入: {process_info["user_input"]}

任务规划:
{json.dumps(process_info["task_planning"], ensure_ascii=False, indent=2, cls=CustomJSONEncoder)}

工具选择:
{json.dumps(process_info["tool_selection"], ensure_ascii=False, indent=2, cls=CustomJSONEncoder)}

任务执行:
{json.dumps(process_info["task_execution"], ensure_ascii=False, indent=2, cls=CustomJSONEncoder)}

请基于以上信息生成最终回复。
"""

    @classmethod
    async def create_streaming_response(
        cls,
        message: str,
        process_info: dict[str, Any],
        chat_history: list[dict[str, object]] | None = None,
    ) -> AsyncGenerator[str, None]:
        try:
            prompt = cls._create_response_prompt(process_info)
            messages: list[dict[str, object]] = [{"role": "system", "content": prompt}]
            if chat_history:
                messages.extend(chat_history)
            messages.append({"role": "user", "content": message})

            router = ProviderRouter()
            if "fake_chat_provider" in router.degraded_modes:
                text = cls._fallback_response(message, process_info)
            else:
                result = await router.chat(json.dumps(messages, ensure_ascii=False))
                text = str(result.content)
            for start in range(0, len(text), 16):
                yield redact_pii(text[start : start + 16])
        except Exception as exc:
            logger.error("Error during XiaoLin reply: %s", exc, exc_info=True)
            yield "抱歉，生成回复时出现错误。"

    @classmethod
    async def create_simple_streaming_response(
        cls,
        message: str,
        chat_history: list[dict[str, object]] | None = None,
    ) -> AsyncGenerator[str, None]:
        process_info = {
            "user_input": message,
            "task_planning": {},
            "tool_selection": {},
            "task_execution": {},
        }
        async for chunk in cls.create_streaming_response(message, process_info, chat_history):
            yield chunk

    @classmethod
    async def create_response(
        cls,
        message: str,
        process_info: dict[str, Any],
        chat_history: list[dict[str, object]] | None = None,
    ) -> str:
        chunks = [
            chunk
            async for chunk in cls.create_streaming_response(message, process_info, chat_history)
        ]
        return "".join(chunks)

    @classmethod
    def _fallback_response(cls, message: str, process_info: dict[str, Any]) -> str:
        if message.strip().lower() in {"你好", "您好", "嗨", "hello", "hi", "在吗"}:
            return "你好，我是浙商小林，可以帮你查询校园信息、规划校园事务，也能协助整理活动方案。"

        successful_results = [
            result.get("api_result", {})
            for result in process_info.get("task_execution", {}).values()
            if isinstance(result, dict) and result.get("status") == "success"
        ]
        evidence_items: list[dict[str, Any]] = []
        for api_result in successful_results:
            data = api_result.get("data")
            if isinstance(data, list):
                evidence_items.extend(item for item in data if isinstance(item, dict))
            elif isinstance(data, dict):
                return cls._dict_result_response(data)

        if not evidence_items:
            return "我这边暂时没有查到准确信息。你可以补充具体时间、地点或事项，我再帮你继续查。"

        excerpts = [str(item.get("excerpt") or item.get("title") or "") for item in evidence_items[:4]]
        excerpts = [item for item in excerpts if item]
        if any(keyword in message for keyword in ("规划", "安排", "讲座", "活动", "场地")):
            lines = ["可以，我先按查到的信息给你整理一个可执行方案："]
            for index, excerpt in enumerate(excerpts[:3], start=1):
                lines.append(f"{index}. {excerpt}")
            lines.append("下一步建议你确认日期、时段和审批口径；未提供的联系人、宿舍、手机号等个人信息我不会代填。")
            return "\n".join(lines)
        return "\n".join(excerpts)

    @staticmethod
    def _dict_result_response(data: dict[str, Any]) -> str:
        if data.get("title") or data.get("body"):
            return f"草稿标题：{data.get('title', '')}\n{data.get('body', '')}\n草稿尚未发布，需要你确认后才能发布。"
        if data.get("status") == "success" and isinstance(data.get("booking"), dict):
            booking = data["booking"]
            return (
                f"已生成待审批的场地预约草稿：{booking.get('venue_name', '')}，"
                f"{booking.get('date', '')} {booking.get('period', '')}。尚未提交，需要你明确确认。"
            )
        return json.dumps(data, ensure_ascii=False)
