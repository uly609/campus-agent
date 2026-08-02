from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.domain.schemas import CommunityAuditEvent, ModerationReviewCreate, PostReport
from app.services.community_service import CommunityService
from app.services.repository import JsonRepository

router = APIRouter(prefix="/api/v1/community", tags=["community"])
repo = JsonRepository()
service = CommunityService(repo)


@router.get("/moderation/reports", response_model=list[PostReport])
def moderation_queue(
    status: str | None = Query(default="pending_review", pattern="^(pending_review|resolved)$"),
) -> list[PostReport]:
    return repo.load_reports(status=status)


@router.post("/moderation/reports/{report_id}/review", response_model=PostReport)
def review_report(report_id: str, payload: ModerationReviewCreate) -> PostReport:
    report = service.review_report(report_id, payload)
    if report is None:
        raise HTTPException(status_code=404, detail={"code": "REPORT_NOT_FOUND"})
    return report


@router.get("/audit", response_model=list[CommunityAuditEvent])
def community_audit(limit: int = Query(default=100, ge=1, le=500)) -> list[CommunityAuditEvent]:
    return repo.load_community_audit()[:limit]
