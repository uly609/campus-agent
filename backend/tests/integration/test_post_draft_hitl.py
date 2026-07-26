from __future__ import annotations

import pytest

from app.domain.enums import PostCategory
from app.services.post_service import (
    MAX_EDIT_ROUNDS,
    apply_feedback,
    create_draft,
    draft_to_dict,
    publish_confirmed_draft,
)
from app.services.repository import JsonRepository


@pytest.mark.parametrize(
    ("intent", "expected"),
    [
        ("在南门捡到一张校园卡", PostCategory.LOST_FOUND),
        ("转让九成新显示器", PostCategory.SECOND_HAND),
        ("周五去高铁站找人拼车", PostCategory.CARPOOL),
        ("期末找数据库学习搭子", PostCategory.STUDY),
        ("组织周末羽毛球活动报名", PostCategory.EVENT),
        ("求助：校园网怎么报修", PostCategory.QA),
        ("吐槽宿舍热水供应时间", PostCategory.RANT),
        ("分享食堂新窗口体验", PostCategory.LIFE),
    ],
)
def test_draft_classifies_campus_post_scenarios(
    intent: str,
    expected: PostCategory,
) -> None:
    draft = create_draft(intent)
    assert draft.category == expected.value
    assert draft.title
    assert draft.body
    assert draft.tags


def test_draft_accepts_explicit_category_and_optional_image() -> None:
    draft = create_draft("发布学院迎新通知", requested_category=PostCategory.EVENT)
    assert draft.category == PostCategory.EVENT.value
    assert draft.title == "学院迎新通知"
    assert draft.location is None


def test_chat_style_event_request_extracts_topic_instead_of_copying_command() -> None:
    draft = create_draft("帮我写一篇周五学院迎新活动的帖子")
    assert draft.category == PostCategory.EVENT.value
    assert draft.title == "周五学院迎新活动"
    assert "帮我写" not in draft.body
    assert "欢迎感兴趣的同学参加" in draft.body


def test_hitl_draft_enforces_five_edit_rounds_and_confirmation() -> None:
    draft = create_draft("失物招领", {"category": "校园卡", "color": "蓝色", "location_hints": ["图书馆"]})
    for index in range(MAX_EDIT_ROUNDS):
        result = apply_feedback(draft.draft_id, f"补充描述 {index}")
        assert result["ok"]
    blocked = apply_feedback(draft.draft_id, "第六次修改")
    assert blocked["error_code"] == "MAX_EDIT_ROUNDS_REACHED"
    confirmed = apply_feedback(draft.draft_id, "", confirm=True)
    assert confirmed["ok"]
    assert confirmed["requires_user_post_call"]


def test_confirmed_draft_publishes_once(tmp_path) -> None:
    repo = JsonRepository(tmp_path)
    draft = create_draft("周五晚七点学院迎新活动", requested_category=PostCategory.EVENT)
    assert publish_confirmed_draft(draft.draft_id, repo) is None
    assert apply_feedback(draft.draft_id, "", confirm=True)["ok"]

    published = publish_confirmed_draft(draft.draft_id, repo)
    repeated = publish_confirmed_draft(draft.draft_id, repo)

    assert published is not None
    assert repeated is not None
    assert repeated.post_id == published.post_id
    assert len(repo.load_posts()) == 1
    assert draft_to_dict(draft)["published"] is True
