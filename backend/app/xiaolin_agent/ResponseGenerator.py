from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.xiaolin_agent.services.llm_service import LLMService, MAIN_AGENT_MODEL
from app.xiaolin_agent.services.student_profile_service import format_student_profile_for_prompt

logger = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: object) -> object:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()  # type: ignore[no-any-return,attr-defined]
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


class ResponseGenerator:
    """Generate XiaoLin's final user-facing response."""

    _CAMPUS_RETRIEVAL_MARKERS = (
        "浙江工商大学",
        "浙商大",
        "学校",
        "校园",
        "下沙校区",
        "教工路校区",
        "图书馆",
        "课表",
        "课程",
        "教室",
        "老师",
        "教师",
        "校长",
        "校园卡",
        "一卡通",
        "宿舍",
        "食堂",
        "校医院",
        "教务",
        "奖学金",
        "志愿活动",
        "场地",
        "开放时间",
    )

    @classmethod
    def _student_profile_prompt(cls) -> str:
        return format_student_profile_for_prompt()

    @classmethod
    def _create_response_prompt(cls, process_info: dict[str, Any]) -> str:
        return f"""你是浙江工商大学智能校园助手「浙小商助手」。你的回答要自然、亲切、简洁，像一位靠谱的校园服务同学在和用户聊天。

回答风格：
1. 先直接回应用户的问题，不要绕到“我准备如何处理”。
2. 简单寒暄、问候、闲聊时，用1-2句轻松回应即可，不要自我介绍过长。
3. 涉及校园事务时保持准确、清楚、友好；信息不足时自然说明，并给出可行建议。
4. 可以少量使用emoji，但不要连续堆叠，不要显得刻意卖萌。
5. 除非用户明确要求，否则不要暴露任务规划、工具选择、工具名称、服务器状态、调用失败、内部错误等处理过程。
6. 如果工具结果为空、失败或不可用，请基于已有信息给出自然回复；无法确定时说“我这边暂时没有查到准确信息”，不要提“工具/服务器/MCP/任务失败”。
7. 不要重复用户原话来凑字数，不要说“刚才我收到了你的问候”这类流程化表达。
8. 严格区分数据来源：`synthetic_demo: true` 或 `data_mode: demo` 只能称为“演示数据”，不得描述成用户真实课表、真实预约状态或学校当前规定。
9. 只有 `data_mode: verified_official` 的资料可以称为学校官方来源；回答时应给出其标题、URL和核验日期。`live_external: true` 只能称为实时外部数据。
10. 如果任务结果只是通用模型生成、没有可验证来源，禁止补写具体地点、时间、人物、电话、办理流程或当前状态。

以下是当前用户的学生画像，只供你理解用户背景和提供个性化校园服务，不要主动完整展示：
{cls._student_profile_prompt()}

以下过程信息只供你理解上下文，不要原样展示给用户：
**过程信息：**
用户输入: {process_info['user_input']}

任务规划:
{json.dumps(process_info['task_planning'], ensure_ascii=False, indent=2, cls=CustomJSONEncoder)}

工具选择:
{json.dumps(process_info['tool_selection'], ensure_ascii=False, indent=2, cls=CustomJSONEncoder)}

任务执行:
{json.dumps(process_info['task_execution'], ensure_ascii=False, indent=2, cls=CustomJSONEncoder)}

请基于以上信息生成最终回复。
"""

    @classmethod
    def _create_simple_response_prompt(cls) -> str:
        return f"""你是浙江工商大学智能校园助手「浙小商助手」。请用自然、亲切、简洁的方式回答用户。
简单问候和通用知识可以直接回答。普通模式没有调用校园知识库、学校官网、课表、通知或场地工具。
当用户询问浙江工商大学的具体地点、开放时间、人员、电话、规章、办理流程、课表、通知、场地或其他可能变化的校园事实时：
1. 不得凭模型记忆或聊天历史猜测具体答案。
2. 明确说明普通模式没有检索校园资料，建议用户开启 Agent 查询，或前往相应学校官网核对。
3. 不要编造公众号、App、小程序、建筑方位、教师姓名、课程、时间或联系方式。
可以少量使用emoji，但不要过度卖萌，不要暴露内部错误。

以下是当前用户的演示学生画像，只用于界面功能演示，不代表已连接真实学籍或教务系统，不要把其中内容说成用户真实信息：
{cls._student_profile_prompt()}"""

    @classmethod
    def _requires_campus_retrieval(cls, message: str) -> bool:
        return any(marker in message for marker in cls._CAMPUS_RETRIEVAL_MARKERS)

    @classmethod
    async def create_streaming_response(
        cls,
        message: str,
        process_info: dict[str, Any],
        chat_history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        try:
            llm = await LLMService.get_llm(model_name=MAIN_AGENT_MODEL, stream=True)
            prompt = cls._create_response_prompt(process_info)
            messages: list[dict[str, str]] = [{"role": "system", "content": prompt}]
            if chat_history:
                messages.extend(chat_history)
            messages.append({"role": "user", "content": message})
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield str(chunk.content)
        except Exception:
            logger.error("Error during reply", exc_info=True)
            yield "抱歉，生成回复时出现错误。"

    @classmethod
    async def create_simple_streaming_response(
        cls,
        message: str,
        chat_history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        if cls._requires_campus_retrieval(message):
            yield (
                "普通模式没有检索校园资料，我不能据此确认学校的具体信息。"
                "请开启 Agent 查询；如果结果标注为“演示数据”，仍需以浙江工商大学官网或校内系统为准。"
            )
            return
        try:
            llm = await LLMService.get_llm(model_name=MAIN_AGENT_MODEL, stream=True)
            system_prompt = cls._create_simple_response_prompt()
            messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
            if chat_history:
                messages.extend(chat_history)
            messages.append({"role": "user", "content": message})
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield str(chunk.content)
        except Exception:
            logger.error("Error during simple reply", exc_info=True)
            yield "抱歉，生成回复时出现错误。"

    @classmethod
    async def create_response(
        cls,
        message: str,
        process_info: dict[str, Any],
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        try:
            llm = await LLMService.get_llm(model_name=MAIN_AGENT_MODEL, temperature=0.7)
            prompt = cls._create_response_prompt(process_info)
            messages: list[dict[str, str]] = [{"role": "system", "content": prompt}]
            if chat_history:
                messages.extend(chat_history)
            messages.append({"role": "user", "content": message})
            response = await llm.ainvoke(messages)
            return str(response.content)
        except Exception:
            logger.error("生成响应过程出错", exc_info=True)
            return "抱歉，在处理您的请求时出现了问题。请稍后再试。"
