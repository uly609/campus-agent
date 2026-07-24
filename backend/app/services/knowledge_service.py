git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
from __future__ import annotations

import hashlib
import uuid
from typing import Any

from app.core.redis import get_redis_client
from app.domain.platform_schemas import IngestionJob, KnowledgeDocument, KnowledgeDocumentCreate
from app.retrieval.ingestion import build_corpus
from app.retrieval.service import RetrievalService
from app.services.repository import JsonRepository, now_iso

INGESTION_STREAM = "campusflow:knowledge:ingest"


class DuplicateKnowledgeError(ValueError):
    pass


class KnowledgeService:
    def __init__(self, repository: JsonRepository | None = None, redis_client: Any | None = None) -> None:
        self.repository = repository or JsonRepository()
        self.redis = redis_client or get_redis_client()

    def enqueue(self, payload: KnowledgeDocumentCreate) -> IngestionJob:
        content_hash = hashlib.sha256(payload.body.strip().encode("utf-8")).hexdigest()
        duplicate = next(
            (item for item in self.repository.load_knowledge() if item.content_hash == content_hash),
            None,
        )
        if duplicate and duplicate.source_id != payload.source_id:
            raise DuplicateKnowledgeError(duplicate.source_id)

        timestamp = now_iso()
        existing = next(
            (item for item in self.repository.load_knowledge() if item.source_id == payload.source_id),
            None,
        )
        document = KnowledgeDocument(
            **payload.model_dump(),
            status="queued",
            content_hash=content_hash,
            chunk_count=0,
            created_at=existing.created_at if existing else timestamp,
            updated_at=timestamp,
        )
        self.repository.save_knowledge(document)
        job = IngestionJob(
            job_id=f"ingest-{uuid.uuid4().hex[:12]}",
            source_id=payload.source_id,
            status="queued",
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.repository.save_ingestion_job(job)
        self.redis.xadd(
            INGESTION_STREAM,
            {"job_id": job.job_id, "source_id": job.source_id, "created_at": timestamp},
            maxlen=1000,
            approximate=True,
        )
        return job

    async def process(self, job_id: str) -> IngestionJob:
        job = self.repository.find_ingestion_job(job_id)
        if job is None:
            raise KeyError("INGESTION_JOB_NOT_FOUND")
        document = next(
            (item for item in self.repository.load_knowledge() if item.source_id == job.source_id),
            None,
        )
        if document is None:
            return self._fail(job, "KNOWLEDGE_DOCUMENT_NOT_FOUND", "知识文档不存在")

        job = job.model_copy(
            update={
                "status": "processing",
                "progress": 15,
                "attempt": job.attempt + 1,
                "updated_at": now_iso(),
                "error_code": None,
                "error_message": None,
            }
        )
        self.repository.save_ingestion_job(job)
        self.repository.save_knowledge(
            document.model_copy(update={"status": "indexing", "updated_at": now_iso(), "error_code": None})
        )
        try:
            runtime_document = {
                "source_id": document.source_id,
                "source_type": document.source_type,
                "title": document.title,
                "body": document.body,
                "official": "true" if document.official else "false",
                "path": document.path,
                "url": document.url,
            }
            runtime_docs = [
                row for row in self.repository.load_documents() if row.get("source_id") != document.source_id
            ]
            runtime_docs.append(runtime_document)
            self.repository.save_documents(runtime_docs)
            job = job.model_copy(update={"progress": 60, "updated_at": now_iso()})
            self.repository.save_ingestion_job(job)

            service = RetrievalService(build_corpus(self.repository.load_posts(), runtime_docs))
            await service.rebuild()
            chunk_count = len([chunk for chunk in service.chunks if chunk.source_id == document.source_id])
            self.repository.save_knowledge(
                document.model_copy(
                    update={
                        "status": "ready",
                        "chunk_count": chunk_count,
                        "updated_at": now_iso(),
                        "error_code": None,
                    }
                )
            )
            job = job.model_copy(
                update={"status": "completed", "progress": 100, "updated_at": now_iso()}
            )
            return self.repository.save_ingestion_job(job)
        except (OSError, RuntimeError, ValueError) as exc:
            return self._fail(job, "INGESTION_FAILED", str(exc)[:240])

    def retry(self, job_id: str) -> IngestionJob:
        job = self.repository.find_ingestion_job(job_id)
        if job is None:
            raise KeyError("INGESTION_JOB_NOT_FOUND")
        if job.status != "failed":
            raise ValueError("INGESTION_JOB_NOT_FAILED")
        if job.attempt >= job.max_attempts:
            raise ValueError("INGESTION_RETRY_EXHAUSTED")
        queued = job.model_copy(
            update={
                "status": "queued",
                "progress": 0,
                "error_code": None,
                "error_message": None,
                "updated_at": now_iso(),
            }
        )
        self.repository.save_ingestion_job(queued)
        self.redis.xadd(
            INGESTION_STREAM,
            {"job_id": queued.job_id, "source_id": queued.source_id, "created_at": now_iso()},
            maxlen=1000,
            approximate=True,
        )
        return queued

    def delete(self, source_id: str) -> bool:
        deleted = self.repository.delete_knowledge(source_id)
        runtime_docs = [
            row for row in self.repository.load_documents() if row.get("source_id") != source_id
        ]
        self.repository.save_documents(runtime_docs)
        return deleted

    def _fail(self, job: IngestionJob, code: str, message: str) -> IngestionJob:
        document = next(
            (item for item in self.repository.load_knowledge() if item.source_id == job.source_id),
            None,
        )
        if document:
            self.repository.save_knowledge(
                document.model_copy(update={"status": "failed", "error_code": code, "updated_at": now_iso()})
            )
        failed = job.model_copy(
            update={
                "status": "failed",
                "error_code": code,
                "error_message": message,
                "updated_at": now_iso(),
            }
        )
        return self.repository.save_ingestion_job(failed)
