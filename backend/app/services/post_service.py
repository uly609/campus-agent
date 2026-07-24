from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import PostCategory
from app.domain.schemas import Post, PostCreate
from app.security.content_policy import check_post_safety
from app.services.repository import JsonRepository

MAX_EDIT_ROUNDS = 5


@dataclass
class DraftSession:
    draft_id: str
    title: str
    body: str
    category: str
    tags: list[str]
    location: str | None = None
    edit_round: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    confirmed: bool = False


_drafts: dict[str, DraftSession] = {}


_CATEGORY_KEYWORDS: tuple[tuple[PostCategory, tuple[str, ...]], ...] = (
    (PostCategory.LOST_FOUND, ("失物", "招领", "捡到", "丢失", "遗失", "找回")),
    (PostCategory.SECOND_HAND, ("二手", "出售", "转让", "求购", "闲置", "出掉")),
    (PostCategory.CARPOOL, ("拼车", "顺风车", "同行", "车友")),
    (PostCategory.STUDY, ("学习搭子", "自习", "组队学习", "复习搭子", "刷题")),
    (PostCategory.EVENT, ("活动", "报名", "讲座", "比赛", "社团", "招新")),
    (PostCategory.QA, ("求助", "请问", "咨询", "怎么", "哪里", "有没有人知道")),
    (PostCategory.RANT, ("吐槽", "建议", "反馈", "不合理")),
)


def classify_post_category(intent: str) -> PostCategory:
    normalized = intent.strip().lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return category
    return PostCategory.LIFE


def _image_context(attrs: dict[str, Any]) -> tuple[str, str, str]:
    hints = attrs.get("location_hints", [])
    location = str(hints[0]).strip() if isinstance(hints, list) and hints else ""
    item = str(attrs.get("category", "")).strip()
    color = str(attrs.get("color", "")).strip()
    return location, item, f"{color}{item}".strip()


def _intent_summary(intent: str) -> str:
    summary = intent.strip().strip("，。！？ ")
    for prefix in ("帮我", "请帮我", "起草", "写一条", "发一条", "发布", "一条"):
        if summary.startswith(prefix):
            summary = summary.removeprefix(prefix).strip(" ：:")
    return summary.split("，", 1)[0].split("。", 1)[0][:32]


def _draft_content(
    intent: str,
    category: PostCategory,
    attrs: dict[str, Any],
) -> tuple[str, str, list[str], str | None]:
    location, item, descriptor = _image_context(attrs)
    request = intent.strip() or "分享一条校园动态"
    summary = _intent_summary(request)
    place = location or "校园"
    subject = descriptor or item or "相关信息"

    if category == PostCategory.LOST_FOUND:
        title = f"{place}失物招领：{subject}" if descriptor else f"失物招领：{summary}"
        body = (
            f"在{place}附近发现{subject}。请失主描述物品细节后联系认领。"
            if descriptor
            else f"{request}。请知情同学通过站内方式联系，并注意核对物品细节。"
        )
        tags = ["失物招领", item or "物品", place]
    elif category == PostCategory.SECOND_HAND:
        title = f"二手转让：{subject}" if descriptor else f"二手：{summary.removeprefix('转让')}"
        body = f"{request}。物品情况和交易方式请私信确认，建议在校内公共区域当面交易。"
        tags = ["二手", item or "闲置", place]
    elif category == PostCategory.CARPOOL:
        title = f"拼车：{summary}"
        body = f"{request}。请沟通出发时间、集合地点和费用分摊，注意核验同行人员信息。"
        tags = ["拼车", "同行", place]
    elif category == PostCategory.STUDY:
        title = f"学习搭子：{summary}"
        body = f"{request}。希望一起明确学习时间和目标，互相监督并按时复盘。"
        tags = ["学习", "搭子", place]
    elif category == PostCategory.EVENT:
        title = summary or (f"{location}校园活动" if location else "校园活动")
        body = f"{request}。请在参与前确认时间、地点、报名方式和主办方通知。"
        tags = ["活动", "报名", place]
    elif category == PostCategory.QA:
        title = f"校园求助：{summary.removeprefix('求助').strip(' ：:')}"
        body = f"{request}。欢迎了解情况的同学提供可靠信息或官方办理渠道。"
        tags = ["校园问答", "求助", place]
    elif category == PostCategory.RANT:
        title = f"校园建议：{summary.removeprefix('吐槽').strip(' ：:')}"
        body = f"{request}。希望大家理性讨论，也欢迎补充可行的改进建议。"
        tags = ["吐槽", "建议", place]
    else:
        title = summary or f"{place}生活分享"
        body = f"{request}。欢迎同学们交流相关经历和实用信息。"
        tags = ["生活", "校园", place]
    return title[:80], body[:2000], tags, location or None


def create_draft(
    intent: str,
    image_attributes: dict[str, Any] | None = None,
    requested_category: PostCategory | None = None,
) -> DraftSession:
    attrs = image_attributes or {}
    category = requested_category or classify_post_category(intent)
    title, body, tags, location = _draft_content(intent, category, attrs)
    draft_id = f"draft-{len(_drafts) + 1:04d}"
    draft = DraftSession(
        draft_id=draft_id,
        title=title,
        body=body,
        category=category.value,
        tags=tags,
        location=location,
    )
    draft.history.append(
        {
            "round": 0,
            "intent": intent,
            "category": category.value,
            "title": draft.title,
            "body": draft.body,
        }
    )
    _drafts[draft_id] = draft
    return draft


def apply_feedback(draft_id: str, feedback: str, confirm: bool = False) -> dict[str, Any]:
    if draft_id not in _drafts:
        return {"ok": False, "error_code": "DRAFT_NOT_FOUND"}
    draft = _drafts[draft_id]
    if confirm:
        policy = check_post_safety(draft.title, draft.body)
        if not policy["allowed"]:
            return {"ok": False, "error_code": policy["error_code"], "flags": policy["flags"]}
        draft.confirmed = True
        return {"ok": True, "draft": draft_to_dict(draft), "published": False, "requires_user_post_call": True}
    if draft.edit_round >= MAX_EDIT_ROUNDS:
        return {"ok": False, "error_code": "MAX_EDIT_ROUNDS_REACHED", "max_rounds": MAX_EDIT_ROUNDS}
    before = f"{draft.title}\n{draft.body}"
    draft.edit_round += 1
    if "标题" in feedback:
        draft.title = feedback.replace("标题", "").replace("改成", "").strip(" ：:")[:80] or draft.title
    else:
        addition = feedback.strip()
        for prefix in ("正文", "补充", "加一句"):
            if addition.startswith(prefix):
                addition = addition.removeprefix(prefix).strip(" ：:")
        if addition:
            draft.body = f"{draft.body}\n{addition[:120]}"
    after = f"{draft.title}\n{draft.body}"
    diff = "\n".join(difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm=""))
    draft.history.append({"round": draft.edit_round, "feedback": feedback, "diff": diff})
    return {"ok": True, "draft": draft_to_dict(draft), "diff": diff}


def publish_confirmed_draft(draft_id: str, repo: JsonRepository | None = None) -> Post | None:
    draft = _drafts.get(draft_id)
    if not draft or not draft.confirmed:
        return None
    active_repo = repo or JsonRepository()
    return active_repo.create_post(
        PostCreate(
            title=draft.title,
            body=draft.body,
            category=PostCategory(draft.category),
            tags=draft.tags,
            location=draft.location,
            images=[],
        )
    )


def draft_to_dict(draft: DraftSession) -> dict[str, Any]:
    return {
        "draft_id": draft.draft_id,
        "title": draft.title,
        "body": draft.body,
        "category": draft.category,
        "tags": draft.tags,
        "location": draft.location,
        "edit_round": draft.edit_round,
        "max_edit_rounds": MAX_EDIT_ROUNDS,
        "history": draft.history,
        "confirmed": draft.confirmed,
    }
