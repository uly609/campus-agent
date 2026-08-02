from __future__ import annotations

import math
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Literal

from app.domain.schemas import (
    CommunityAuditEvent,
    FeedPost,
    ModerationReviewCreate,
    Post,
    PostReport,
    PostReportCreate,
)
from app.services.repository import JsonRepository, now_iso

FeedMode = Literal["latest", "hot", "for_you"]

REASON_WEIGHTS = {
    "spam": 0.45,
    "abuse": 0.7,
    "fraud": 0.9,
    "privacy": 0.8,
    "inaccurate": 0.4,
    "other": 0.3,
}
HIGH_RISK_TERMS = ("身份证", "银行卡", "验证码", "转账", "裸照", "人肉", "手机号")


class CommunityService:
    """Deterministic community ranking and human-reviewed moderation."""

    def __init__(self, repo: JsonRepository | None = None) -> None:
        self.repo = repo or JsonRepository()

    def _age_hours(self, post: Post) -> float:
        try:
            created = datetime.fromisoformat(post.created_at.replace("Z", "+00:00"))
            return max(0.0, (datetime.now(timezone.utc) - created).total_seconds() / 3600)
        except ValueError:
            return 720.0

    def _engagement(self, post: Post) -> tuple[int, int, int]:
        return (
            self.repo.count_likes(post.post_id),
            self.repo.count_comments(post.post_id),
            self.repo.count_reports(post.post_id),
        )

    def _affinity(self, user_id: str) -> Counter[str]:
        liked_ids = {
            row.post_id
            for row in self.repo.load_reactions()
            if row.user_id == user_id and row.liked
        }
        affinity: Counter[str] = Counter()
        for post in self.repo.load_posts():
            if post.post_id not in liked_ids:
                continue
            affinity[f"category:{post.category.value}"] += 2
            affinity.update(f"tag:{tag}" for tag in post.tags)
        return affinity

    def _feed_post(self, post: Post, user_id: str, mode: FeedMode, affinity: Counter[str]) -> FeedPost:
        likes, comments, reports = self._engagement(post)
        freshness = 8 * math.exp(-self._age_hours(post) / 168)
        hot_score = freshness + 2 * likes + 3 * comments - 4 * reports
        affinity_score = affinity[f"category:{post.category.value}"]
        affinity_score += sum(affinity[f"tag:{tag}"] for tag in post.tags)
        score = hot_score + (2.5 * affinity_score if mode == "for_you" else 0)
        if mode == "latest":
            reason = "按发布时间排序"
        elif mode == "for_you" and affinity_score:
            reason = "与你点赞过的分类或标签相关"
        elif mode == "for_you":
            reason = "暂无偏好数据，先按校园热度推荐"
        else:
            reason = "综合新鲜度、点赞和评论热度"
        return FeedPost(
            **post.model_dump(exclude={"comment_count"}),
            comment_count=comments,
            like_count=likes,
            report_count=reports,
            viewer_liked=self.repo.user_liked_post(post.post_id, user_id),
            ranking_score=round(score, 4),
            ranking_reason=reason,
        )

    def feed(self, user_id: str, mode: FeedMode = "latest") -> list[FeedPost]:
        hidden = self.repo.hidden_post_ids()
        affinity = self._affinity(user_id)
        posts = [post for post in self.repo.load_posts() if post.post_id not in hidden]
        rows = [self._feed_post(post, user_id, mode, affinity) for post in posts]
        if mode != "latest":
            rows.sort(key=lambda row: (row.ranking_score, row.created_at), reverse=True)
        return rows

    def get_post(self, post_id: str, user_id: str) -> FeedPost | None:
        return next((post for post in self.feed(user_id) if post.post_id == post_id), None)

    def create_report(self, post: Post, payload: PostReportCreate) -> PostReport:
        existing = next(
            (
                report
                for report in self.repo.load_reports()
                if report.post_id == post.post_id
                and report.user_id == payload.user_id
                and report.status == "pending_review"
            ),
            None,
        )
        if existing:
            return existing
        text = f"{post.title}\n{post.body}\n{payload.detail}"
        extra = 0.15 if any(term in text for term in HIGH_RISK_TERMS) else 0
        score = min(1.0, REASON_WEIGHTS[payload.reason] + extra)
        suggestion: Literal["keep", "review", "hide"] = "keep"
        if score >= 0.8:
            suggestion = "hide"
        elif score >= 0.45:
            suggestion = "review"
        report = PostReport(
            **payload.model_dump(),
            report_id=f"report-{uuid.uuid4().hex[:10]}",
            post_id=post.post_id,
            risk_score=score,
            suggested_decision=suggestion,
            created_at=now_iso(),
        )
        self.repo.save_report(report)
        self.repo.append_community_audit(
            CommunityAuditEvent(
                event_id=f"audit-{uuid.uuid4().hex[:10]}",
                action="report_created",
                actor_alias=payload.user_id,
                post_id=post.post_id,
                report_id=report.report_id,
                detail={"reason": payload.reason, "risk_score": score, "suggestion": suggestion},
                created_at=now_iso(),
            )
        )
        return report

    def review_report(self, report_id: str, payload: ModerationReviewCreate) -> PostReport | None:
        report = self.repo.resolve_report(report_id, payload)
        if report is None:
            return None
        self.repo.append_community_audit(
            CommunityAuditEvent(
                event_id=f"audit-{uuid.uuid4().hex[:10]}",
                action="report_reviewed",
                actor_alias=payload.reviewer_alias,
                post_id=report.post_id,
                report_id=report.report_id,
                detail={"decision": payload.decision, "note": payload.note},
                created_at=now_iso(),
            )
        )
        return report
