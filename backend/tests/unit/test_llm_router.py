from __future__ import annotations

import pytest

from app.llm.providers.fake import FakeChatProvider
from app.llm.router import ProviderRouter


@pytest.mark.asyncio
async def test_router_falls_back_on_recoverable_errors() -> None:
    router = ProviderRouter()
    router.chat_providers = [FakeChatProvider("local_primary", should_fail=True), FakeChatProvider("local_backup")]
    result = await router.chat("图书馆几点关门")
    assert result.provider == "local_backup"
    assert router.trace[0]["status"] == "failed"

