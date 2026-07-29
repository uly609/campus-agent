from __future__ import annotations

import pytest

from app.core.config import Settings
from app.llm.providers.fake import FakeChatProvider
from app.llm.router import ProviderRouter


class NonFakeChatProvider:
    is_fake = False
    name = "cloud_fallback"
    model = "qwen-plus"

    async def complete(self, prompt: str) -> str:
        raise AssertionError("cached provider should not be called")


@pytest.mark.asyncio
async def test_router_falls_back_on_recoverable_errors() -> None:
    router = ProviderRouter()
    router.chat_providers = [FakeChatProvider("local_primary", should_fail=True), FakeChatProvider("local_backup")]
    result = await router.chat("图书馆几点关门")
    assert result.provider == "local_backup"
    assert router.trace[0]["status"] == "failed"


def test_router_uses_one_bailian_key_for_all_cloud_roles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        dashscope_api_key="one-bailian-key",
        cloud_fallback_chat_url="https://example.com/v1",
        cloud_fallback_embedding_url="https://example.com/v1",
        cloud_fallback_vlm_url="https://example.com/v1",
    )
    monkeypatch.setattr("app.llm.router.get_settings", lambda: settings)

    router = ProviderRouter()

    for provider in (
        router.chat_providers[0],
        router.embedding_providers[0],
        router.vlm_providers[0],
    ):
        assert provider._headers["Authorization"] == "Bearer one-bailian-key"


@pytest.mark.asyncio
async def test_real_provider_cache_hit_is_not_marked_degraded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = ProviderRouter()
    router.chat_providers = [NonFakeChatProvider()]
    monkeypatch.setattr(router.cache, "get", lambda key: "cached response")

    result = await router.chat("你好")

    assert result.cache_hit is True
    assert result.degraded is False
