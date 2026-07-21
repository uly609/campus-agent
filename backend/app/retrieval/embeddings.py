from __future__ import annotations

import hashlib
import math
from typing import Protocol

from app.retrieval.chunking import tokenize

BGE_M3_DIMENSIONS = 1024


class EmbeddingProvider(Protocol):
    provider_name: str

    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class DeterministicBgeM3CompatibleEmbedding:
    provider_name = "fake-bge-m3-compatible"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [embed_text(text) for text in texts]


def embed_text(text: str) -> list[float]:
    vector = [0.0] * BGE_M3_DIMENSIONS
    tokens = tokenize(text)
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % BGE_M3_DIMENSIONS
        sign = -1.0 if digest[4] % 2 else 1.0
        vector[bucket] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 6) for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))

