from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

from app.agent.planner.planner import StructuredPlanner
from app.domain.schemas import ChatRequest, ChatResponse, GroundedAnswer
from app.llm.router import ProviderRouter
from app.memory.producer import publish_memory_event
from app.memory.recall import recall_relevant_memories
from app.security.pii import redact_pii
from app.services.repository import JsonRepository, now_iso
from app.xiaolin_agent.LLMController import get_process_info
from app.xiaolin_agent.ResponseGenerator import ResponseGenerator

repo = JsonRepository()


def _remember_event(process_info: dict[str, Any], event: dict[str, Any]) -> None:
    if event.get("type") == "step":
        process_info.setdefault("steps", []).append(str(event.get("content", "")))
        return
    if event.get("type") != "data":
        return
    subtype = event.get("subtype")
    content = event.get("content")
    if subtype == "task_plan":
        process_info["task_planning"] = {"tasks": content}
    elif subtype == "tool_selections":
        process_info["tool_selection"] = {"tool_selections": content}
    elif subtype == "task_result" and isinstance(content, dict):
        process_info.setdefault("task_execution", {})[int(content["task_id"])] = content[
            "result"
        ]
    elif subtype == "process_summary" and isinstance(content, dict):
        process_info.clear()
        process_info.update(content)


def _trace_event(event: dict[str, Any]) -> dict[str, Any]:
    if event.get("type") == "step":
        return {"event": "xiaolin_step", "content": event.get("content")}
    return {
        "event": str(event.get("subtype", "xiaolin_data")),
        "content": event.get("content"),
    }


async def stream_xiaolin_events(request: ChatRequest) -> AsyncGenerator[dict[str, Any], None]:
    memories = recall_relevant_memories(
        request.message, repo.load_memories(request.user_id), top_k=3
    )
    process_info: dict[str, Any] = {
        "user_input": request.message,
        "steps": [],
        "task_planning": {},
        "tool_selection": {},
        "task_execution": {},
    }
    trace: list[dict[str, Any]] = []
    async for event in get_process_info(request.message, request.user_id, memories):
        _remember_event(process_info, event)
        trace.append(_trace_event(event))
        yield event

    full_response = ""
    async for chunk in ResponseGenerator.create_streaming_response(
        request.message, process_info, memories
    ):
        if chunk:
            text = redact_pii(str(chunk))
            full_response += text
            yield {"content": text}

    intent = StructuredPlanner().fallback_plan(request.message, request.user_id).intent
    publish_memory_event(
        user_id=request.user_id,
        session_id=request.session_id,
        text=request.message,
        source="xiaolin_chat",
    )
    repo.append_trace(
        {
            "request_id": f"req-{uuid.uuid4().hex[:12]}",
            "session_id": request.session_id,
            "user_id": request.user_id,
            "created_at": now_iso(),
            "engine": "xiaolin_planner_selector_executor",
            "intent": intent.value,
            "trace": trace,
        }
    )


async def run_xiaolin(request: ChatRequest) -> ChatResponse:
    text = ""
    trace: list[dict[str, Any]] = []
    async for event in stream_xiaolin_events(request):
        if "content" in event and event.get("type") is None:
            text += str(event["content"])
        else:
            trace.append(_trace_event(event))
    intent = StructuredPlanner().fallback_plan(request.message, request.user_id).intent
    return ChatResponse(
        request_id=f"req-{uuid.uuid4().hex[:12]}",
        answer=GroundedAnswer(answer=text, confidence=0.7),
        intent=intent,
        citations=[],
        trace=trace,
        degraded_mode=ProviderRouter().degraded_modes,
    )
