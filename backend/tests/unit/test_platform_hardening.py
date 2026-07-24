from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.core.redis import InMemoryRedis
from app.domain.platform_schemas import KnowledgeDocumentCreate, ProviderProfileCreate
from app.services.knowledge_service import DuplicateKnowledgeError, KnowledgeService
from app.services.provider_registry import ProviderRegistry
from app.services.repository import JsonRepository


class FakeRetrievalService:
    def __init__(self, chunks: list[Any]) -> None:
        self.chunks = chunks

    async def rebuild(self) -> None:
        return None


@pytest.mark.asyncio
async def test_knowledge_ingestion_tracks_job_and_deduplicates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.services.knowledge_service.RetrievalService",
        FakeRetrievalService,
    )
    repository = JsonRepository(tmp_path)
    redis = InMemoryRedis()
    service = KnowledgeService(repository, redis)
    payload = KnowledgeDocumentCreate(
        source_id="official-library",
        title="图书馆开放时间",
        body="图书馆工作日开放时间为 08:00 至 22:00。",
    )

    job = service.enqueue(payload)
    completed = await service.process(job.job_id)

    assert completed.status == "completed"
    assert completed.progress == 100
    assert repository.load_knowledge()[0].status == "ready"
    assert redis.xrange("campusflow:knowledge:ingest")
    with pytest.raises(DuplicateKnowledgeError):
        service.enqueue(payload.model_copy(update={"source_id": "duplicate-library"}))


def test_provider_credentials_are_encrypted_and_public_output_is_redacted(tmp_path: Path) -> None:
    repository = JsonRepository(tmp_path)
    registry = ProviderRegistry(repository, encryption_secret="unit-test-secret")
    created = registry.create(
        ProviderProfileCreate(
            name="测试云模型",
            role="chat",
            tier="cloud_fallback",
            base_url="https://models.example/v1",
            model="test-chat",
            api_key="secret-api-key",
        )
    )

    stored = repository.load_provider_profiles()[0]
    assert created.api_key_present is True
    assert "secret-api-key" not in (stored.api_key_ciphertext or "")
    assert registry.runtime_specs("chat")[0][3] == "secret-api-key"
    assert "api_key_ciphertext" not in created.model_dump()


def test_in_memory_redis_supports_fixed_window_rate_limit_primitives() -> None:
    redis = InMemoryRedis()
    assert redis.incr("rate:key") == 1
    assert redis.expire("rate:key", 60) is True
    assert redis.incr("rate:key") == 2
