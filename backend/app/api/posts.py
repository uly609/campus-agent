from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.domain.schemas import Post, PostCreate, SearchRequest
from app.multimodal.image_attributes import enhance_query_with_image, extract_image_attributes
from app.retrieval.ingestion import build_corpus
from app.retrieval.service import RetrievalService
from app.services.post_service import apply_feedback, create_draft, draft_to_dict, publish_confirmed_draft
from app.services.repository import JsonRepository

router = APIRouter(prefix="/api/v1")
repo = JsonRepository()


class DraftRequest(BaseModel):
    intent: str
    image_url: str | None = None


class DraftFeedback(BaseModel):
    feedback: str = ""
    confirm: bool = False
    publish: bool = False


@router.post("/posts", response_model=Post)
def create_post(payload: PostCreate) -> Post:
    return repo.create_post(payload)


@router.get("/posts", response_model=list[Post])
def list_posts() -> list[Post]:
    return repo.load_posts()[:80]


@router.get("/posts/{post_id}", response_model=Post)
def get_post(post_id: str) -> Post:
    post = repo.find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND"})
    return post


@router.post("/posts/search")
async def search_posts(payload: SearchRequest) -> dict[str, Any]:
    query = payload.query
    if payload.image_attributes:
        query = enhance_query_with_image(query, payload.image_attributes)
    service = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    results = await service.search(query, payload.top_k)
    return {"query": query, "results": [item.model_dump() for item in results]}


@router.post("/posts/draft")
async def draft(payload: DraftRequest) -> dict[str, Any]:
    attrs = {}
    if payload.image_url:
        attrs = await extract_image_attributes(payload.image_url)
    return {"draft": draft_to_dict(create_draft(payload.intent, attrs)), "image_attributes": attrs}


@router.post("/posts/draft/{draft_id}/feedback")
def draft_feedback(draft_id: str, payload: DraftFeedback) -> dict[str, Any]:
    result = apply_feedback(draft_id, payload.feedback, confirm=payload.confirm)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result)
    if payload.publish:
        post = publish_confirmed_draft(draft_id, repo)
        if post is None:
            raise HTTPException(status_code=409, detail={"code": "DRAFT_NOT_CONFIRMED"})
        result["post"] = post.model_dump()
    return result

