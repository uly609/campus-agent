from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.domain.schemas import ChatRequest, ChatResponse
from app.services.chat_service import handle_chat

router = APIRouter(prefix="/api/v1")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await handle_chat(request)


@router.get("/chat/{session_id}/events")
async def chat_events(session_id: str) -> StreamingResponse:
    async def event_stream():
        events = [
            {"event": "accepted", "session_id": session_id},
            {"event": "node_started", "node": "coreference_resolver_node"},
            {"event": "node_finished", "node": "coreference_resolver_node"},
            {"event": "tool_called", "tool": "search_campus_docs"},
            {"event": "citation", "source_id": "doc-library-hours-00"},
            {"event": "token", "text": "这是带引用的校园回答。"},
            {"event": "completed"},
        ]
        for event in events:
            yield f"event: {event['event']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.01)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

