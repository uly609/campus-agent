from __future__ import annotations

from app.domain.enums import PostCategory
from app.domain.schemas import ModerationReviewCreate, PostCreate, PostReportCreate
from app.services.community_service import CommunityService
from app.services.repository import JsonRepository


def _post(repo: JsonRepository, title: str, category: PostCategory, tags: list[str]):
    return repo.create_post(
        PostCreate(
            title=title,
            body=f"{title}的正文内容",
            category=category,
            tags=tags,
        )
    )


def test_like_is_idempotent_and_changes_feed_score(tmp_path) -> None:
    repo = JsonRepository(tmp_path)
    service = CommunityService(repo)
    first = _post(repo, "羽毛球约球", PostCategory.EVENT, ["羽毛球"])
    second = _post(repo, "高数复习交流", PostCategory.STUDY, ["高数"])

    repo.set_post_like(first.post_id, "u1", True)
    repo.set_post_like(first.post_id, "u1", True)
    repo.set_post_like(first.post_id, "u2", True)

    feed = service.feed("u3", "hot")
    assert feed[0].post_id == first.post_id
    assert feed[0].like_count == 2
    assert next(row for row in feed if row.post_id == second.post_id).like_count == 0


def test_for_you_uses_liked_categories_and_tags(tmp_path) -> None:
    repo = JsonRepository(tmp_path)
    service = CommunityService(repo)
    liked = _post(repo, "羽毛球入门", PostCategory.EVENT, ["羽毛球"])
    related = _post(repo, "周末羽毛球", PostCategory.EVENT, ["羽毛球"])
    _post(repo, "二手台灯", PostCategory.SECOND_HAND, ["台灯"])
    repo.set_post_like(liked.post_id, "u1", True)

    feed = service.feed("u1", "for_you")
    related_result = next(row for row in feed if row.post_id == related.post_id)
    assert "分类或标签" in related_result.ranking_reason
    assert related_result.ranking_score > 0


def test_report_requires_human_review_before_post_is_hidden(tmp_path) -> None:
    repo = JsonRepository(tmp_path)
    service = CommunityService(repo)
    post = _post(repo, "疑似诈骗信息", PostCategory.SECOND_HAND, ["交易"])

    report = service.create_report(
        post,
        PostReportCreate(user_id="u1", reason="fraud", detail="要求先转账并发送验证码"),
    )
    assert report.suggested_decision == "hide"
    assert post.post_id not in repo.hidden_post_ids()

    reviewed = service.review_report(
        report.report_id,
        ModerationReviewCreate(decision="hide", reviewer_alias="管理员", note="人工确认诈骗"),
    )
    assert reviewed is not None
    assert reviewed.final_decision == "hide"
    assert post.post_id in repo.hidden_post_ids()
    assert [event.action for event in repo.load_community_audit()] == [
        "report_reviewed",
        "report_created",
    ]


def test_duplicate_pending_report_returns_existing_record(tmp_path) -> None:
    repo = JsonRepository(tmp_path)
    service = CommunityService(repo)
    post = _post(repo, "广告测试帖子", PostCategory.LIFE, ["广告"])
    payload = PostReportCreate(user_id="u1", reason="spam")

    first = service.create_report(post, payload)
    second = service.create_report(post, payload)

    assert first.report_id == second.report_id
    assert len(repo.load_reports()) == 1
