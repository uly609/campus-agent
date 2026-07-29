from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.domain.schemas import ChatRequest
from app.xiaolin_agent.LLMController import get_process_info
from app.xiaolin_agent.ResponseGenerator import ResponseGenerator
from app.xiaolin_agent.services.chat_history_manager import ChatHistoryManager

logger = logging.getLogger(__name__)


async def stream_xiaolin_events(request: ChatRequest) -> AsyncGenerator[dict[str, Any], None]:
    """Run the same streaming chat lifecycle as the upstream XiaoLin endpoint."""
    message = request.message.strip()
    session_id = request.session_id
    user_message = await ChatHistoryManager.save_message(
        session_id=session_id,
        user_id=request.user_id,
        content=message,
        is_user=True,
    )
    if not user_message:
        raise RuntimeError("更新聊天历史请求失败")

    chat_history = await ChatHistoryManager.get_chat_history(session_id)
    full_response = ""
    process_steps: list[str] = []
    task_plan: list[dict[str, Any]] | None = None
    tool_selections: dict[int, dict[str, Any]] | None = None
    task_results: dict[int, Any] = {}
    process_info: dict[str, Any] | None = None

    try:
        if request.is_agent:
            async for event in get_process_info(message):
                yield event
                if event.get("type") == "step":
                    process_steps.append(str(event.get("content", "")))
                elif event.get("type") == "data":
                    subtype = event.get("subtype")
                    content = event.get("content")
                    if subtype == "task_plan" and isinstance(content, list):
                        task_plan = content
                    elif subtype == "task_result" and isinstance(content, dict):
                        task_results[int(content.get("task_id", 0))] = content.get("result")
                    elif subtype == "tool_selections" and isinstance(content, dict):
                        tool_selections = content

            process_info = {
                "user_input": message,
                "steps": process_steps,
                "task_planning": {"tasks": task_plan} if task_plan else {},
                "tool_selection": {"tool_selections": tool_selections}
                if tool_selections
                else {},
                "task_execution": task_results,
            }
            async for chunk in ResponseGenerator.create_streaming_response(
                message,
                process_info,
                chat_history,
            ):
                if chunk:
                    full_response += chunk
                    yield {"content": chunk}
        else:
            async for chunk in ResponseGenerator.create_simple_streaming_response(
                message,
                chat_history,
            ):
                if chunk:
                    full_response += chunk
                    yield {"content": chunk}
    finally:
        if full_response:
            ai_message = await ChatHistoryManager.save_message(
                session_id=session_id,
                user_id=request.user_id,
                content=full_response,
                is_user=False,
            )
            if request.is_agent and process_info:
                await ChatHistoryManager.save_process_info(
                    message_id=str(ai_message["id"]),
                    session_id=session_id,
                    process_info=process_info,
                )
        logger.info("小林聊天流结束: %s", session_id)
