from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.domain.platform_schemas import SourceDetail
from app.services.repository import JsonRepository

router = APIRouter(prefix="/api/v1")
repo = JsonRepository()


@router.get("/sources/{source_id}", response_model=SourceDetail)
def get_source_detail(source_id: str) -> SourceDetail:
    post = repo.find_post(source_id)
    if post is not None:
        return SourceDetail(
            source_id=post.post_id,
            source_type="post",
            title=post.title,
            body=post.body,
            official=False,
            location=post.location,
            tags=post.tags,
            author_alias=post.author_alias,
            created_at=post.created_at,
        )

    document = next(
        (item for item in repo.load_documents() if item.get("source_id") == source_id),
        None,
    )
    if document is None:
        raise HTTPException(status_code=404, detail={"code": "SOURCE_NOT_FOUND"})
    return SourceDetail(
        source_id=document["source_id"],
        source_type="official" if document.get("official", "true") == "true" else "post",
        title=document["title"],
        body=document["body"],
        official=document.get("official", "true") == "true",
        url=document.get("url") or None,
    )
