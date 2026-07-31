from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.domain.platform_schemas import FileParseOut, KnowledgeDocumentCreate, ParsedFileChunkOut
from app.multimodal.document_parser import parse_document_file
from app.services.knowledge_service import DuplicateKnowledgeError, KnowledgeService
from app.services.repository import JsonRepository

router = APIRouter(prefix="/api/v1")
repo = JsonRepository()
service = KnowledgeService(repo)
MAX_INGEST_BODY_CHARS = 200_000


def _ingest_body(chunks: list[ParsedFileChunkOut]) -> str:
    body = "\n\n---\n\n".join(f"[{chunk.kind}] {chunk.title}\n{chunk.text}" for chunk in chunks)
    if len(body) > MAX_INGEST_BODY_CHARS:
        body = body[:MAX_INGEST_BODY_CHARS].rstrip() + "\n\n[内容过长，已截断]"
    return body


@router.post("/files/parse", response_model=FileParseOut)
async def parse_file(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    ingest: Annotated[bool, Form()] = False,
    official: Annotated[bool, Form()] = False,
    title: Annotated[str | None, Form()] = None,
) -> FileParseOut:
    filename = file.filename or "upload"
    content = await file.read()
    try:
        result = await parse_document_file(filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "FILE_PARSE_FAILED", "detail": str(exc)}) from exc

    payload = FileParseOut(
        file_name=result.file_name,
        kind=result.kind,
        chunks=[ParsedFileChunkOut(**chunk.__dict__) for chunk in result.chunks],
        warnings=result.warnings,
    )
    if not ingest:
        return payload
    source_id = f"kb-file-{uuid.uuid4().hex[:10]}"
    document_title = (title or Path(filename).stem).strip() or "校园文件"
    if len(document_title) < 2:
        document_title = f"{document_title} 文件"
    document = KnowledgeDocumentCreate(
        source_id=source_id,
        title=document_title[:160],
        body=_ingest_body(payload.chunks),
        source_type="official",
        official=official,
        path=filename,
    )
    try:
        job = service.enqueue(document)
    except DuplicateKnowledgeError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "DUPLICATE_KNOWLEDGE", "existing_source_id": str(exc)},
        ) from exc
    background_tasks.add_task(service.process, job.job_id)
    payload.source_id = source_id
    payload.job_id = job.job_id
    return payload
