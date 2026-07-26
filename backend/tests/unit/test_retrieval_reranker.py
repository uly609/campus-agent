from __future__ import annotations

import json

import httpx
import pytest

from app.retrieval.chunking import Chunk
from app.retrieval.reranker import RetrievalReranker


def chunk(source_id: str, title: str, text: str) -> Chunk:
    return Chunk(source_id, source_id, "official", title, text, True, {})


@pytest.mark.asyncio
async def test_qwen_reranker_uses_provider_scores_and_threshold() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "qwen3-rerank"
        assert payload["query"] == "教学楼在哪里"
        return httpx.Response(
            200,
            json={
                "results": [
                    {"index": 1, "relevance_score": 0.92},
                    {"index": 0, "relevance_score": 0.08},
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        reranker = RetrievalReranker(client)
        reranker.url = "https://model.test/compatible-api/v1/reranks"
        reranker.api_key = "test-key"
        reranker.min_score = 0.25
        results = await reranker.rerank(
            "教学楼在哪里",
            [
                chunk("bus", "校车", "北门通勤车每天发车。"),
                chunk("building", "教学楼位置", "教学楼 A 位于中心广场东侧。"),
            ],
            5,
        )

    assert [item.chunk.source_id for item in results] == ["building"]
    assert results[0].mode == "qwen3-rerank"


@pytest.mark.asyncio
async def test_fallback_drops_location_evidence_about_the_wrong_subject() -> None:
    reranker = RetrievalReranker()
    reranker.url = None
    reranker.api_key = None
    results = await reranker.rerank(
        "教学楼在哪里",
        [chunk("bus", "校车与通勤车", "北门至主校区通勤车 7:20 发车。")],
        5,
    )

    assert results == []


@pytest.mark.asyncio
async def test_qwen_score_cannot_promote_a_mention_that_does_not_answer_location() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"index": 0, "relevance_score": 0.99}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        reranker = RetrievalReranker(client)
        reranker.url = "https://model.test/compatible-api/v1/reranks"
        reranker.api_key = "test-key"
        results = await reranker.rerank(
            "教学楼在哪里",
            [chunk("lost", "教学楼 A 附近捡到雨伞", "失主请联系认领。地点:教学楼A")],
            5,
        )

    assert results == []
