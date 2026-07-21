from __future__ import annotations

import pytest

from app.domain.schemas import ChatRequest
from app.services.chat_service import handle_chat
from scripts.seed import main as seed_main


@pytest.mark.asyncio
async def test_chat_flow_returns_citations_and_trace() -> None:
    seed_main()
    response = await handle_chat(ChatRequest(message="图书馆今天几点关门？"))
    assert response.citations
    assert any(item["event"] == "node_finished" for item in response.trace)
    assert "fake_chat_provider" in response.degraded_mode

