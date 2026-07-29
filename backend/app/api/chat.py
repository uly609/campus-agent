from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.domain.platform_schemas import UserSession
from app.domain.schemas import ChatRequest
from app.services.chat_service import handle_chat
from app.services.repository import JsonRepository, now_iso
from app.services.xiaolin_service import stream_xiaolin_events

router = APIRouter(prefix="/api/v1")
repo = JsonRepository()


def _save_session(request: ChatRequest) -> None:
    existing = next(
        (
            item
            for item in repo.load_sessions(request.user_id)
            if item.session_id == request.session_id
        ),
        None,
    )
    timestamp = now_iso()
    repo.save_session(
        UserSession(
            session_id=request.session_id,
            user_id=request.user_id,
            title=(
                request.message[:32]
                if existing is None or (existing.title == "新对话" and existing.message_count == 0)
                else existing.title
            ),
            message_count=(existing.message_count if existing else 0) + 1,
            created_at=existing.created_at if existing else timestamp,
            updated_at=timestamp,
        )
    )


@router.post("/chat", response_model=None)
@router.post("/chat/", response_model=None)
async def chat(request: ChatRequest):
    if request.is_agent:
        return chat_stream(request)
    response = await handle_chat(request)
    _save_session(request)
    return response


@router.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    async def event_stream():
        try:
            async for event in stream_xiaolin_events(request):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as exc:
            error = {"type": "error", "content": str(exc)}
            yield f"data: {json.dumps(error, ensure_ascii=False)}\n\n"

    _save_session(request)
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/chat/{session_id}/events")
async def chat_events(session_id: str) -> StreamingResponse:
    async def event_stream():
        event = {"event": "accepted", "session_id": session_id}
        yield f"event: accepted\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.01)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
