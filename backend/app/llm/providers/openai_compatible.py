from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from app.llm.base import ProviderRecoverableError


def _endpoint(base_url: str, resource: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith(resource):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/{resource}"
    return f"{normalized}/v1/{resource}"


class OpenAICompatibleProvider:
    is_fake = False

    def __init__(
        self,
        name: str,
        model: str,
        base_url: str,
        api_key: str | None,
        timeout_seconds: float,
        max_retries: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.name = name
        self.model = model
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, max_retries)
        self._client = client
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

    async def _post(self, resource: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_error = "unknown provider error"
        for attempt in range(self.max_retries + 1):
            try:
                if self._client is not None:
                    response = await self._client.post(
                        _endpoint(self.base_url, resource), headers=self._headers, json=payload
                    )
                else:
                    async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                        response = await client.post(
                            _endpoint(self.base_url, resource), headers=self._headers, json=payload
                        )
                response.raise_for_status()
                body = response.json()
                if not isinstance(body, dict):
                    raise ValueError("provider response is not an object")
                return body
            except (httpx.HTTPError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
                last_error = f"{exc.__class__.__name__}: {exc}"
                if attempt < self.max_retries:
                    await asyncio.sleep(min(0.1 * (2**attempt), 0.8))
        raise ProviderRecoverableError(f"{self.name} failed after bounded retries: {last_error}")


class OpenAICompatibleChatProvider(OpenAICompatibleProvider):
    async def complete(self, prompt: str) -> str:
        body = await self._post(
            "chat/completions",
            {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
        )
        content = body["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ProviderRecoverableError(f"{self.name} returned empty chat content")
        return content


class OpenAICompatibleEmbeddingProvider(OpenAICompatibleProvider):
    async def embed(self, text: str) -> list[float]:
        return (await self.embed_many([text]))[0]

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        body = await self._post("embeddings", {"model": self.model, "input": texts})
        data = body.get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise ProviderRecoverableError(f"{self.name} returned an invalid embedding batch")
        ordered = sorted(data, key=lambda item: int(item.get("index", 0)))
        embeddings: list[list[float]] = []
        try:
            for item in ordered:
                vector = item["embedding"]
                if not isinstance(vector, list) or not vector:
                    raise ValueError("empty embedding")
                embeddings.append([float(value) for value in vector])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderRecoverableError(f"{self.name} returned non-numeric embedding values") from exc
        return embeddings


class OpenAICompatibleVLMProvider(OpenAICompatibleProvider):
    async def analyze(self, image_url: str, prompt: str) -> dict[str, object]:
        body = await self._post(
            "chat/completions",
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_url}},
                            {
                                "type": "text",
                                "text": (
                                    f"{prompt} Return only a JSON object with category, color, brand, "
                                    "material, visible_text, location_hints, confidence, and safety_flags. "
                                    "All descriptive values and location hints must use concise Simplified Chinese."
                                ),
                            },
                        ],
                    }
                ],
                "temperature": 0,
            },
        )
        content = body["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise ProviderRecoverableError(f"{self.name} returned invalid VLM content")
        cleaned = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ProviderRecoverableError(f"{self.name} returned non-JSON VLM content") from exc
        if not isinstance(parsed, dict):
            raise ProviderRecoverableError(f"{self.name} returned a non-object VLM result")
        return parsed
