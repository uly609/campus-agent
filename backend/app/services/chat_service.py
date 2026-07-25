from __future__ import annotations

from app.agent.graph import run_agent
from app.domain.enums import Intent
from app.domain.schemas import ChatRequest, ChatResponse, Citation, GroundedAnswer
from app.security.pii import redact_pii
from app.services.conversation_context import load_last_query, save_last_query


async def handle_chat(request: ChatRequest) -> ChatResponse:
    previous_query = load_last_query(request.user_id, request.session_id)
    state = await run_agent(
        request.message,
        request.session_id,
        request.user_id,
        request.image_urls,
        previous_query,
    )
    save_last_query(request.user_id, request.session_id, redact_pii(request.message))
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
