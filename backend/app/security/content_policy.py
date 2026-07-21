from __future__ import annotations


def check_post_safety(title: str, body: str) -> dict[str, object]:
    text = f"{title}\n{body}"
    blocked = [word for word in ["人肉", "泄露隐私", "辱骂"] if word in text]
    return {"allowed": not blocked, "flags": blocked, "error_code": "CONTENT_POLICY_BLOCK" if blocked else None}

