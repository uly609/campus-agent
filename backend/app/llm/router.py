from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from app.llm.base import ProviderRecoverableError, ProviderResult
from app.llm.cache import ExactMatchCache
from app.llm.providers.fake import FakeChatProvider, FakeEmbeddingProvider, FakeVLMProvider
from app.observability.metrics import CACHE_HITS, LLM_CALLS, LLM_FAILURES, LLM_LATENCY


class ProviderRouter:
    def __init__(self) -> None:
        self.cache = ExactMatchCache()
        self.chat_providers = [
            FakeChatProvider("local_primary"),
            FakeChatProvider("local_backup"),
            FakeChatProvider("cloud_fallback"),
        ]
        self.embedding_providers = [
            FakeEmbeddingProvider("local_primary"),
            FakeEmbeddingProvider("local_backup"),
            FakeEmbeddingProvider("cloud_fallback"),
        ]
        self.vlm_providers = [
            FakeVLMProvider("local_primary"),
            FakeVLMProvider("local_backup"),
            FakeVLMProvider("cloud_fallback"),
        ]
        self.trace: list[dict[str, Any]] = []

    async def chat(self, prompt: str) -> ProviderResult:
        return await self._route("chat", self.chat_providers, lambda provider: provider.complete(prompt), prompt)

    async def embed(self, text: str) -> ProviderResult:
        return await self._route("embedding", self.embedding_providers, lambda provider: provider.embed(text), text)

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
            cache_key = self.cache.key(role, provider.model, payload)
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
                degraded = provider.name != "local_primary" or provider.name.startswith("local")
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

