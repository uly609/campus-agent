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
    edit_round: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    confirmed: bool = False


_drafts: dict[str, DraftSession] = {}


def create_draft(intent: str, image_attributes: dict[str, Any] | None = None) -> DraftSession:
    attrs = image_attributes or {}
    location = ""
    hints = attrs.get("location_hints", [])
    if isinstance(hints, list) and hints:
        location = str(hints[0])
    category = str(attrs.get("category", "物品"))
    color = str(attrs.get("color", ""))
    draft_id = f"draft-{len(_drafts) + 1:04d}"
    draft = DraftSession(
        draft_id=draft_id,
        title=f"{location or '校园'}失物招领：{color}{category}",
        body=f"在{location or '校园'}附近发现{color}{category}。请失主描述细节后认领。本草稿需要确认后才会发布。",
        category=PostCategory.LOST_FOUND.value,
        tags=["失物招领", category, location or "校园"],
    )
    draft.history.append({"round": 0, "intent": intent, "title": draft.title, "body": draft.body})
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
        draft.body = f"{draft.body}\n修改{draft.edit_round}: {feedback[:120]}"
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
            location=draft.tags[-1],
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
        "edit_round": draft.edit_round,
        "max_edit_rounds": MAX_EDIT_ROUNDS,
        "history": draft.history,
        "confirmed": draft.confirmed,
    }

