from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.domain.platform_schemas import IngestionJob, KnowledgeDocument, KnowledgeDocumentCreate
from app.domain.schemas import SearchRequest
from app.retrieval.ingestion import build_corpus
from app.retrieval.service import RetrievalService
from app.services.knowledge_service import DuplicateKnowledgeError, KnowledgeService
from app.services.repository import JsonRepository

router = APIRouter(prefix="/api/v1")
repo = JsonRepository()
service = KnowledgeService(repo)


@router.post("/ingest/documents")
async def ingest_document(
    payload: KnowledgeDocumentCreate, background_tasks: BackgroundTasks
) -> dict[str, str]:
    try:
        job = service.enqueue(payload)
    except DuplicateKnowledgeError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "DUPLICATE_KNOWLEDGE", "existing_source_id": str(exc)},
        ) from exc
    background_tasks.add_task(service.process, job.job_id)
    return {"status": "accepted", "source_id": payload.source_id, "job_id": job.job_id}


@router.get("/knowledge/documents", response_model=list[KnowledgeDocument])
def list_knowledge_documents() -> list[KnowledgeDocument]:
    return repo.load_knowledge()


@router.get("/knowledge/jobs", response_model=list[IngestionJob])
def list_ingestion_jobs() -> list[IngestionJob]:
    return repo.load_ingestion_jobs()


@router.get("/knowledge/documents/{source_id}/chunks")
def preview_document_chunks(source_id: str) -> dict[str, object]:
    """Expose the exact chunks used for retrieval in the governance workflow."""
    document = next((item for item in repo.load_documents() if item.get("source_id") == source_id), None)
    if document is None:
        knowledge = next((item for item in repo.load_knowledge() if item.source_id == source_id), None)
        if knowledge is None:
            raise HTTPException(status_code=404, detail={"code": "KNOWLEDGE_DOCUMENT_NOT_FOUND"})
        document = knowledge.model_dump(mode="json")
    chunks = [chunk for chunk in build_corpus([], [document]) if chunk.source_id == source_id]
    return {
        "source_id": source_id,
        "title": document.get("title", ""),
        "version": document.get("version", "v1"),
        "chunk_strategy": "paragraph-aware target_tokens=500 overlap=80",
        "chunks": [
            {"chunk_id": chunk.chunk_id, "title": chunk.title, "text": chunk.text, "metadata": chunk.metadata}
            for chunk in chunks
        ],
    }


@router.post("/retrieval/explain")
async def explain_retrieval(payload: SearchRequest) -> dict[str, object]:
    """Return ranked evidence plus the retrieval route for debugging and evaluation."""
    retrieval = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    evidence = await retrieval.search(payload.query, payload.top_k)
    return {
        "query": payload.query,
        "results": [item.model_dump(mode="json") for item in evidence],
        "explanation": {
            "pipeline": "BM25 + embedding + graph expansion + RRF + rerank",
            "source_route": evidence[0].metadata.get("source_route", "hybrid") if evidence else "hybrid",
            "result_count": len(evidence),
        },
    }


@router.post("/knowledge/documents", response_model=IngestionJob)
async def create_knowledge_document(
    payload: KnowledgeDocumentCreate, background_tasks: BackgroundTasks
) -> IngestionJob:
    try:
        job = service.enqueue(payload)
    except DuplicateKnowledgeError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "DUPLICATE_KNOWLEDGE", "existing_source_id": str(exc)},
        ) from exc
    background_tasks.add_task(service.process, job.job_id)
    return job


@router.post("/knowledge/jobs/{job_id}/retry", response_model=IngestionJob)
async def retry_ingestion_job(job_id: str, background_tasks: BackgroundTasks) -> IngestionJob:
    try:
        job = service.retry(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"code": str(exc.args[0])}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": str(exc)}) from exc
    background_tasks.add_task(service.process, job.job_id)
    return job


@router.delete("/knowledge/documents/{source_id}")
def delete_knowledge_document(source_id: str) -> dict[str, object]:
    if not service.delete(source_id):
        raise HTTPException(status_code=404, detail={"code": "KNOWLEDGE_DOCUMENT_NOT_FOUND"})
    return {"deleted": True, "source_id": source_id}


@router.post("/ingest/rebuild-index")
async def rebuild_index() -> dict[str, object]:
    service = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    await service.rebuild()
    return {"status": "rebuilt", "chunks": len(service.chunks), "neo4j_degraded": service.vector_store.degraded_reason}
