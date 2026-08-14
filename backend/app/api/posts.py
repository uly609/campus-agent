from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.domain.enums import PostCategory
from app.domain.schemas import (
    FeedPost,
    Post,
    PostComment,
    PostCommentCreate,
    PostCreate,
    PostReactionCreate,
    PostReport,
    PostReportCreate,
    SearchRequest,
)
from app.memory.producer import publish_memory_event
from app.multimodal.image_attributes import enhance_query_with_image, extract_image_attributes
from app.retrieval.ingestion import build_corpus
from app.retrieval.service import RetrievalService
from app.services.post_service import (
    apply_feedback,
    create_draft,
    draft_to_dict,
    get_draft,
    publish_confirmed_draft,
)
from app.services.community_service import CommunityService
from app.services.repository import JsonRepository

router = APIRouter(prefix="/api/v1")
repo = JsonRepository()
community = CommunityService(repo)


class DraftRequest(BaseModel):
    intent: str
    image_url: str | None = None
    category: PostCategory | None = None
    user_id: str = "demo-user"
    session_id: str = "post-assistant"


class DraftFeedback(BaseModel):
    feedback: str = ""
    confirm: bool = False
    publish: bool = False


@router.post("/posts", response_model=Post)
def create_post(payload: PostCreate) -> Post:
    return repo.create_post(payload)


@router.get("/posts", response_model=list[FeedPost])
def list_posts(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    mode: Literal["latest", "hot", "for_you"] = "latest",
    user_id: str = Query(default="demo-user", min_length=1, max_length=80),
    domain: str | None = Query(default=None, min_length=2, max_length=40),
) -> list[FeedPost]:
    return community.feed(user_id, mode, domain=domain)[offset : offset + limit]


@router.get("/posts/{post_id}", response_model=FeedPost)
def get_post(post_id: str, user_id: str = "demo-user") -> FeedPost:
    post = community.get_post(post_id, user_id)
    if not post:
        raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND"})
    return post


@router.post("/posts/{post_id}/reactions", response_model=FeedPost)
def react_to_post(post_id: str, payload: PostReactionCreate) -> FeedPost:
    if not repo.find_post(post_id):
        raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND"})
    repo.set_post_like(post_id, payload.user_id, payload.liked)
    post = community.get_post(post_id, payload.user_id)
    if post is None:
        raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND"})
    return post


@router.post("/posts/{post_id}/reports", response_model=PostReport, status_code=201)
def report_post(post_id: str, payload: PostReportCreate) -> PostReport:
    post = repo.find_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND"})
    return community.create_report(post, payload)


@router.get("/posts/{post_id}/comments", response_model=list[PostComment])
def list_comments(post_id: str) -> list[PostComment]:
    if not repo.find_post(post_id):
        raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND"})
    return repo.load_comments(post_id)


@router.post("/posts/{post_id}/comments", response_model=PostComment, status_code=201)
def create_comment(post_id: str, payload: PostCommentCreate) -> PostComment:
    if not repo.find_post(post_id):
        raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND"})
    return repo.create_comment(post_id, payload)


@router.post("/posts/search")
async def search_posts(payload: SearchRequest) -> dict[str, Any]:
    query = payload.query
    if payload.image_attributes:
        query = enhance_query_with_image(query, payload.image_attributes)
    service = RetrievalService(build_corpus(repo.load_posts(), repo.load_documents()))
    results = await service.search(query, payload.top_k, source_type="post")
    return {"query": query, "results": [item.model_dump() for item in results]}


@router.post("/posts/draft")
async def draft(payload: DraftRequest) -> dict[str, Any]:
    attrs = {}
    if payload.image_url:
        attrs = await extract_image_attributes(payload.image_url)
    return {
        "draft": draft_to_dict(
            create_draft(
                payload.intent,
                attrs,
                payload.category,
                user_id=payload.user_id,
                session_id=payload.session_id,
            )
        ),
        "image_attributes": attrs,
    }


@router.post("/posts/draft/{draft_id}/feedback")
def draft_feedback(draft_id: str, payload: DraftFeedback) -> dict[str, Any]:
    if payload.publish:
        post = publish_confirmed_draft(draft_id, repo)
        if post is None:
            raise HTTPException(status_code=409, detail={"code": "DRAFT_NOT_CONFIRMED"})
        current_draft = get_draft(draft_id)
        if current_draft is None:
            raise HTTPException(status_code=404, detail={"code": "DRAFT_NOT_FOUND"})
        if current_draft.memory_event_id is None:
            current_draft.memory_event_id = publish_memory_event(
                user_id=current_draft.user_id,
                session_id=current_draft.session_id,
                text=f"{current_draft.title}\n{current_draft.body}",
                source="published_post",
            )
        return {
            "ok": True,
            "draft": draft_to_dict(current_draft),
            "published": True,
            "post": post.model_dump(),
        }
    result = apply_feedback(draft_id, payload.feedback, confirm=payload.confirm)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result)
    return result
