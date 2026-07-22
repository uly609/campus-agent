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
    assert results[0].metadata["retrieval"] == "bm25+vector+graph+rrf"
    assert "explanation" in results[0].metadata


@pytest.mark.asyncio
async def test_query_expansion_prioritizes_official_card_service_documents() -> None:
    seed_main()
    repo = JsonRepository()
    service = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    results = await service.search("校园卡在哪里补办", top_k=5)
    assert all(result.source_id.startswith("doc-card-loss-") for result in results)
