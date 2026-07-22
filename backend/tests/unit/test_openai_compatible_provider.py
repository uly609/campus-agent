from __future__ import annotations

import httpx
import pytest

from app.llm.providers.openai_compatible import (
    OpenAICompatibleChatProvider,
    OpenAICompatibleEmbeddingProvider,
    OpenAICompatibleVLMProvider,
)


def provider_args(client: httpx.AsyncClient) -> dict[str, object]:
    return {
        "name": "local_primary",
        "model": "test-model",
        "base_url": "http://model.test",
        "api_key": "test-key",
        "timeout_seconds": 1.0,
        "max_retries": 0,
        "client": client,
    }


@pytest.mark.asyncio
async def test_openai_compatible_chat_and_embedding_contracts() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-key"
        if request.url.path.endswith("/embeddings"):
            return httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2, 0.3]}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "grounded"}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        chat = OpenAICompatibleChatProvider(**provider_args(client))
        embedding = OpenAICompatibleEmbeddingProvider(**provider_args(client))
        assert await chat.complete("question") == "grounded"
        assert await embedding.embed("query") == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_openai_compatible_vlm_requires_structured_json() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "```json\n{\"category\": \"校园卡\", \"confidence\": 0.97}\n```"
                        }
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleVLMProvider(**provider_args(client))
        result = await provider.analyze("https://example.test/card.png", "extract")
        assert result["category"] == "校园卡"
        assert result["confidence"] == 0.97
