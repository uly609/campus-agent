from __future__ import annotations

import pytest

from app.llm.router import ProviderRouter


@pytest.mark.asyncio
async def test_exact_match_cache_hits_second_call() -> None:
    router = ProviderRouter()
    first = await router.chat("你好")
    second = await router.chat("你好")
    assert first.content == second.content
    assert second.latency_ms == 0

