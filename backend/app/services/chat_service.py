from __future__ import annotations

from app.agent.graph import run_agent
from app.domain.enums import Intent
from app.domain.schemas import ChatRequest, ChatResponse, Citation, GroundedAnswer
from app.security.pii import redact_pii
from app.services.conversation_context import load_last_query, save_last_query
from app.services.context_compression import ContextCompressionService
from app.services.repository import JsonRepository


repo = JsonRepository()
context_compression = ContextCompressionService(repo=repo)


async def handle_chat(request: ChatRequest) -> ChatResponse:
    context_window = context_compression.load_window(request.session_id, request.user_id)
    previous_query = context_window.virtual_context or load_last_query(request.user_id, request.session_id)
    state = await run_agent(
        request.message,
        request.session_id,
        request.user_id,
        request.image_urls,
        previous_query,
    )
    saved_user_message = repo.save_chat_message(
        {
            "message_id": f"msg-{state['request_id']}-user",
            "session_id": request.session_id,
            "user_id": request.user_id,
            "role": "user",
            "content": redact_pii(request.message),
        }
    )
    repo.save_chat_message(
        {
            "message_id": f"msg-{state['request_id']}-assistant",
            "session_id": request.session_id,
            "user_id": request.user_id,
            "role": "assistant",
            "content": redact_pii(state.get("final_answer", "")),
        }
    )
    save_last_query(request.user_id, request.session_id, saved_user_message["content"])
    scheduled = context_compression.schedule_precompression(request.session_id, request.user_id)
    state.setdefault("trace", []).append(
        {
            "event": "context_window",
            "summary_version": context_window.summary_version,
            "estimated_tokens": context_window.estimated_tokens,
            "recent_message_count": len(context_window.recent_messages),
            "precompression_scheduled": scheduled,
        }
    )
    answer = GroundedAnswer(
        answer=state.get("final_answer", ""),
        claims=[],
        citations=[],
        unsupported_questions=[],
        confidence=0.0 if "证据不足" in state.get("final_answer", "") else 0.75,
    )
    if state.get("citations"):
        answer.citations = [Citation.model_validate(item) for item in state["citations"]]
    return ChatResponse(
        request_id=state["request_id"],
        answer=answer,
        intent=Intent(state.get("intent", Intent.CAMPUS_QA.value)),
        citations=answer.citations,
        trace=state.get("trace", []),
        degraded_mode=state.get("degraded_mode", []),
    )
