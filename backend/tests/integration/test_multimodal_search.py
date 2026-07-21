from __future__ import annotations

import pytest

from app.multimodal.image_attributes import extract_image_attributes
from app.retrieval.ingestion import build_corpus
from app.retrieval.service import RetrievalService
from app.services.repository import JsonRepository
from scripts.seed import main as seed_main


@pytest.mark.asyncio
async def test_multimodal_search_uses_image_attributes() -> None:
    seed_main()
    attrs = await extract_image_attributes("synthetic-card-library-blue.png")
    service = RetrievalService(build_corpus(JsonRepository().load_posts(), JsonRepository().load_documents()))
    results = await service.search(f"失物 {attrs['category']} {attrs['color']}", top_k=8)
    assert results

