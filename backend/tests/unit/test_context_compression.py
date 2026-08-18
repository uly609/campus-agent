from __future__ import annotations

import pytest

from app.llm.base import ProviderRecoverableError
from app.services.context_compression import ContextCompressionService
from app.services.repository import JsonRepository


class StubResult:
    degraded = False
    content = '{"completed_tasks":["完成需求澄清"],"constraints":["回答简洁"],"facts":[],"tool_conclusions":[],"open_items":[],"citations":[]}'


class StubRouter:
    async def chat(self, _prompt: str) -> StubResult:
        return StubResult()


@pytest.mark.asyncio
async def test_progressive_context_compression_keeps_summary_and_recent_window(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CONTEXT_COMPRESSION_ENABLED", "true")
    repo = JsonRepository(tmp_path)
    for index in range(8):
        repo.save_chat_message(
            {
                "message_id": f"m-{index}",
                "session_id": "s1",
                "user_id": "u1",
                "role": "user" if index % 2 == 0 else "assistant",
                "content": f"第 {index} 轮对话内容，包含需要保留的约束。",
            }
        )
    service = ContextCompressionService(repo=repo, router=StubRouter())
    service.max_tokens = 10
    service.trigger_ratio = 0.5
    service.recent_limit = 2

    before = service.load_window("s1", "u1")
    assert before.should_precompress is True
    snapshot = await service.precompress("s1", "u1")

    assert snapshot is not None
    assert snapshot["version"] == 1
    assert snapshot["compressed_through"] == 6
    after = service.load_window("s1", "u1")
    assert after.summary_version == 1
    assert "completed_tasks" in after.summary
    assert [item["message_id"] for item in after.recent_messages] == ["m-6", "m-7"]
    assert len(repo.load_chat_messages("s1")) == 8


@pytest.mark.asyncio
async def test_failed_summary_keeps_previous_snapshot(tmp_path) -> None:
    repo = JsonRepository(tmp_path)
    repo.save_context_snapshot(
        {
            "snapshot_id": "ctx-1",
            "session_id": "s1",
            "user_id": "u1",
            "version": 2,
            "summary": "old summary",
            "compressed_through": 1,
        }
    )
    repo.save_chat_message({"message_id": "m-1", "session_id": "s1", "user_id": "u1", "role": "user", "content": "新内容"})

    class FailingRouter:
        async def chat(self, _prompt: str) -> StubResult:
            raise ProviderRecoverableError("provider unavailable")

    service = ContextCompressionService(repo=repo, router=FailingRouter())
    result = await service.precompress("s1", "u1")
    assert result is not None
    assert result["version"] == 2
    assert repo.load_context_snapshot("s1")["summary"] == "old summary"
