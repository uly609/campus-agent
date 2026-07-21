from __future__ import annotations

import re


def redact_student_card_text(text: str) -> str:
    text = re.sub(r"\b\d{8,14}\b", "[REDACTED_STUDENT_ID]", text)
    text = re.sub(r"(姓名[:：]\s*)[\u4e00-\u9fffA-Za-z]{1,8}", r"\1[REDACTED_NAME]", text)
    return text


def is_synthetic_demo_image(image_url: str) -> bool:
    lowered = image_url.lower()
    return "synthetic" in lowered or "demo" in lowered or "card" in lowered

