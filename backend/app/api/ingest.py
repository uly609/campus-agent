from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.retrieval.ingestion import build_corpus
from app.retrieval.service import RetrievalService
from app.services.repository import JsonRepository

router = APIRouter(prefix="/api/v1")
repo = JsonRepository()


class DocumentPayload(BaseModel):
    source_id: str
    title: str
    body: str
    official: bool = True
    path: str = ""
    url: str = ""


@router.post("/ingest/documents")
def ingest_document(payload: DocumentPayload) -> dict[str, str]:
    docs = repo.load_documents()
    docs.append(
        {
            "source_id": payload.source_id,
            "source_type": "official" if payload.official else "post",
            "title": payload.title,
            "body": payload.body,
            "official": "true" if payload.official else "false",
            "path": payload.path,
            "url": payload.url,
        }
    )
    repo.save_documents(docs)
    return {"status": "accepted", "source_id": payload.source_id}


@router.post("/ingest/rebuild-index")
async def rebuild_index() -> dict[str, object]:
    service = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    await service.rebuild()
    return {"status": "rebuilt", "chunks": len(service.chunks), "neo4j_degraded": service.vector_store.degraded_reason}

