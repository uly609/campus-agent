from __future__ import annotations

from dataclasses import dataclass
import httpx

from app.core.config import get_settings
from app.retrieval.chunking import Chunk, tokenize
from app.retrieval.query_facets import text_matches_query_facet


@dataclass(frozen=True)
class RankedChunk:
    chunk: Chunk
    score: float
    mode: str


class RetrievalReranker:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        settings = get_settings()
        configured_url = settings.rerank_url or settings.cloud_fallback_chat_url
        self.url = self._rerank_endpoint(configured_url) if configured_url else None
        self.api_key = settings.rerank_api_key or settings.openai_api_key
        self.model = settings.rerank_model
        self.min_score = settings.rerank_min_score
        self.timeout = settings.provider_timeout_seconds
        self.client = client
        self.degraded_reason = "" if self.url and self.api_key else "reranker_not_configured"

    @staticmethod
    def _rerank_endpoint(base_url: str) -> str:
        normalized = base_url.rstrip("/")
        normalized = normalized.replace("/compatible-mode/v1", "/compatible-api/v1")
        return normalized if normalized.endswith("/reranks") else f"{normalized}/reranks"

    async def rerank(
        self,
        query: str,
        candidates: list[Chunk],
        top_k: int,
    ) -> list[RankedChunk]:
        unique = list({chunk.source_id: chunk for chunk in candidates}.values())
        if self.url and self.api_key:
            try:
                return await self._qwen_rerank(query, unique, top_k)
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                self.degraded_reason = f"qwen_rerank_failed:{exc.__class__.__name__}"
        return self._lexical_fallback(query, unique, top_k)

    async def _qwen_rerank(
        self,
        query: str,
        candidates: list[Chunk],
        top_k: int,
    ) -> list[RankedChunk]:
        if self.url is None or self.api_key is None:
            raise ValueError("reranker is not configured")
        url = self.url
        api_key = self.api_key
        payload = {
            "model": self.model,
            "query": query,
            "documents": [f"{chunk.title}\n{chunk.text}" for chunk in candidates],
            "top_n": min(top_k, len(candidates)),
            "instruct": "Given a campus question, retrieve passages that explicitly answer the question.",
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        if self.client is not None:
            response = await self.client.post(url, headers=headers, json=payload)
        else:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise ValueError("reranker response is not an object")
        nested = body.get("data") or body.get("output") or {}
        results = body.get("results")
        if results is None and isinstance(nested, dict):
            results = nested.get("results")
        if not isinstance(results, list):
            raise ValueError("reranker response has no results")
        ranked = []
        for item in results:
            index = int(item["index"])
            score = float(item.get("relevance_score", item.get("score", 0.0)))
            if not 0 <= index < len(candidates) or score < self.min_score:
                continue
            chunk = candidates[index]
            if not text_matches_query_facet(query, f"{chunk.title} {chunk.text}"):
                continue
            ranked.append(RankedChunk(chunk, score, self.model))
        return ranked

    @staticmethod
    def _lexical_fallback(query: str, candidates: list[Chunk], top_k: int) -> list[RankedChunk]:
        query_tokens = {
            token for token in tokenize(query) if len(token) >= 2 and token not in QUERY_NOISE_TOKENS
        }
        ranked = []
        for chunk in candidates:
            text = f"{chunk.title} {chunk.text}"
            candidate_tokens = set(tokenize(text))
            overlap = len(query_tokens & candidate_tokens) / max(len(query_tokens), 1)
            if not overlap or not text_matches_query_facet(query, text):
                continue
            ranked.append(RankedChunk(chunk, overlap, "lexical-fallback"))
        return sorted(ranked, key=lambda item: item.score, reverse=True)[:top_k]


QUERY_NOISE_TOKENS = {
    "在哪",
    "哪里",
    "什么",
    "怎么",
    "如何",
    "请问",
    "校园",
    "学校",
    "官方",
    "说明",
    "有没有",
}
