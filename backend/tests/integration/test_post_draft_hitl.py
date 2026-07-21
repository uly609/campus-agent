from __future__ import annotations

from app.services.post_service import MAX_EDIT_ROUNDS, apply_feedback, create_draft


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

