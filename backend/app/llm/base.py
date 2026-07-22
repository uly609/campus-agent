from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ProviderRecoverableError(RuntimeError):
    error_code = "PROVIDER_RECOVERABLE"


class ProviderValidationError(RuntimeError):
    error_code = "PROVIDER_VALIDATION"


@dataclass
class ProviderResult:
    role: str
    provider: str
    model: str
    content: str | list[float] | list[list[float]] | dict[str, object]
    degraded: bool
    latency_ms: int


class ChatProvider(Protocol):
    name: str
    model: str

    async def complete(self, prompt: str) -> str:
        ...


class EmbeddingProviderProtocol(Protocol):
    name: str
    model: str

    async def embed(self, text: str) -> list[float]:
        ...


class VLMProvider(Protocol):
    name: str
    model: str

    async def analyze(self, image_url: str, prompt: str) -> dict[str, object]:
        ...
