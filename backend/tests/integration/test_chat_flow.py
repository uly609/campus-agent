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


@pytest.mark.asyncio
async def test_location_question_answers_with_location_instead_of_hours() -> None:
    seed_main()
    response = await handle_chat(ChatRequest(message="食堂在哪"))
    assert "生活区东侧" in response.answer.answer
    assert "宿舍区南侧" in response.answer.answer
