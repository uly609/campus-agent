from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from app.llm.base import ProviderRecoverableError, ProviderResult
from app.llm.cache import ExactMatchCache
from app.llm.providers.fake import FakeChatProvider, FakeEmbeddingProvider, FakeVLMProvider
from app.llm.providers.openai_compatible import (
    OpenAICompatibleChatProvider,
    OpenAICompatibleEmbeddingProvider,
    OpenAICompatibleVLMProvider,
)
from app.core.config import get_settings
from app.observability.metrics import CACHE_HITS, LLM_CALLS, LLM_FAILURES, LLM_LATENCY


class ProviderRouter:
    def __init__(self) -> None:
        settings = get_settings()
        self.cache = ExactMatchCache()
        common = {"timeout_seconds": settings.provider_timeout_seconds, "max_retries": settings.provider_max_retries}
        self.chat_providers = self._configured(
            OpenAICompatibleChatProvider,
            [
                ("local_primary", settings.local_primary_chat_model, settings.local_primary_chat_url, settings.local_primary_api_key),
                ("local_backup", settings.local_backup_chat_model, settings.local_backup_chat_url, settings.local_backup_api_key),
                ("cloud_fallback", settings.cloud_fallback_chat_model, settings.cloud_fallback_chat_url, settings.openai_api_key),
            ],
            FakeChatProvider("fake_fallback"),
            common,
        )
        self.embedding_providers = self._configured(
            OpenAICompatibleEmbeddingProvider,
            [
                ("local_primary", settings.local_primary_embedding_model, settings.local_primary_embedding_url, settings.local_primary_api_key),
                ("local_backup", settings.local_backup_embedding_model, settings.local_backup_embedding_url, settings.local_backup_api_key),
                ("cloud_fallback", settings.cloud_fallback_embedding_model, settings.cloud_fallback_embedding_url, settings.openai_api_key),
            ],
            FakeEmbeddingProvider("fake_fallback"),
            common,
        )
        self.vlm_providers = self._configured(
            OpenAICompatibleVLMProvider,
            [
                ("local_primary", settings.local_primary_vlm_model, settings.local_primary_vlm_url, settings.local_primary_api_key),
                ("local_backup", settings.local_backup_vlm_model, settings.local_backup_vlm_url, settings.local_backup_api_key),
                ("cloud_fallback", settings.cloud_fallback_vlm_model, settings.cloud_fallback_vlm_url, settings.vlm_api_key or settings.openai_api_key),
            ],
            FakeVLMProvider("fake_fallback"),
            common,
        )
        self.trace: list[dict[str, Any]] = []

    @staticmethod
    def _configured(provider_type: type[Any], specs: list[tuple[str, str, str | None, str | None]], fake: Any, common: dict[str, Any]) -> list[Any]:
        providers = [
            provider_type(name=name, model=model, base_url=url, api_key=key, **common)
            for name, model, url, key in specs
            if url
        ]
        providers.append(fake)
        return providers

    @property
    def degraded_modes(self) -> list[str]:
        modes = []
        if all(getattr(provider, "is_fake", False) for provider in self.chat_providers):
            modes.append("fake_chat_provider")
        if all(getattr(provider, "is_fake", False) for provider in self.embedding_providers):
            modes.append("fake_embedding_provider")
        if all(getattr(provider, "is_fake", False) for provider in self.vlm_providers):
            modes.append("fake_vlm_provider")
        return modes

    async def chat(self, prompt: str) -> ProviderResult:
        return await self._route("chat", self.chat_providers, lambda provider: provider.complete(prompt), prompt)

    async def embed(self, text: str) -> ProviderResult:
        return await self._route("embedding", self.embedding_providers, lambda provider: provider.embed(text), text)

    async def embed_many(self, texts: list[str]) -> ProviderResult:
        return await self._route(
            "embedding",
            self.embedding_providers,
            lambda provider: provider.embed_many(texts),
            texts,
        )

    async def analyze_image(self, image_url: str, prompt: str) -> ProviderResult:
        payload = {"image_url": image_url, "prompt": prompt}
        return await self._route("vlm", self.vlm_providers, lambda provider: provider.analyze(image_url, prompt), payload)

    async def _route(
        self,
        role: str,
        providers: list[Any],
        call: Callable[[Any], Awaitable[Any]],
        payload: Any,
    ) -> ProviderResult:
        for provider in providers:
            cache_key = self.cache.key(role, provider.name, provider.model, payload)
            cached = self.cache.get(cache_key)
            if cached is not None:
                CACHE_HITS.labels(role=role).inc()
                return ProviderResult(role, provider.name, provider.model, cached, True, 0)
            start = time.perf_counter()
            try:
                content = await call(provider)
                latency_ms = int((time.perf_counter() - start) * 1000)
                LLM_CALLS.labels(role=role, provider=provider.name, status="ok").inc()
                LLM_LATENCY.labels(role=role, provider=provider.name).observe(latency_ms / 1000)
                self.cache.set(cache_key, content)
                degraded = bool(getattr(provider, "is_fake", False))
                self.trace.append(
                    {
                        "role": role,
                        "provider": provider.name,
                        "model": provider.model,
                        "status": "ok",
                        "degraded": degraded,
                    }
                )
                return ProviderResult(role, provider.name, provider.model, content, degraded, latency_ms)
            except ProviderRecoverableError as exc:
                latency_ms = int((time.perf_counter() - start) * 1000)
                LLM_CALLS.labels(role=role, provider=provider.name, status="recoverable_error").inc()
                LLM_FAILURES.labels(role=role, provider=provider.name).inc()
                self.trace.append(
                    {
                        "role": role,
                        "provider": provider.name,
                        "model": provider.model,
                        "status": "failed",
                        "reason": str(exc),
                        "latency_ms": latency_ms,
                    }
                )
                continue
        raise ProviderRecoverableError(f"all providers failed for {role}")
