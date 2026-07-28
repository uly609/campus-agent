from __future__ import annotations

import pytest

from app.retrieval.ingestion import build_corpus
from app.retrieval.service import RetrievalService
from app.services.repository import JsonRepository
from scripts.seed import main as seed_main


@pytest.mark.asyncio
async def test_hybrid_retrieval_returns_evidence_with_explanations() -> None:
    seed_main()
    repo = JsonRepository()
    service = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    results = await service.search("图书馆开放时间", top_k=5)
    assert results
    assert "rank-bm25+neo4j-vector+graphrag+rrf" in results[0].metadata["retrieval"]
    assert "explanation" in results[0].metadata


@pytest.mark.asyncio
async def test_query_expansion_prioritizes_official_card_service_documents() -> None:
    seed_main()
    repo = JsonRepository()
    service = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    results = await service.search("校园卡在哪里补办", top_k=5)
    assert all(result.source_id.startswith("doc-card-loss-") for result in results)


@pytest.mark.asyncio
async def test_location_question_prioritizes_location_evidence() -> None:
    seed_main()
    repo = JsonRepository()
    service = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    results = await service.search("食堂在哪", top_k=5)
    assert results[0].source_id.startswith("doc-canteen-")
    assert results[0].official
    assert all(result.metadata["facet_match"] for result in results)
    assert "生活区东侧" in results[0].excerpt


@pytest.mark.asyncio
async def test_timetable_query_prioritizes_timetable_document() -> None:
    seed_main()
    repo = JsonRepository()
    service = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    results = await service.search("课表在哪里看", top_k=5)
    assert results
    assert results[0].source_id.startswith("doc-timetable-")
    assert "我的课表" in results[0].excerpt


@pytest.mark.asyncio
async def test_official_source_route_filters_before_top_k_reranking() -> None:
    service = RetrievalService(build_corpus(JsonRepository().load_posts(), JsonRepository().load_documents()))
    results = await service.search("图书馆今天几点关门？", source_type="official")

    assert results
    assert all(item.official for item in results)
    assert results[0].source_id.startswith("doc-library-hours")
