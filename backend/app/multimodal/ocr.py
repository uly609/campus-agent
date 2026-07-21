from __future__ import annotations

from app.multimodal.privacy import is_synthetic_demo_image, redact_student_card_text


def verify_demo_student_card(image_url: str, visible_text: str) -> dict[str, object]:
    if not is_synthetic_demo_image(image_url):
        return {
            "verified": False,
            "error_code": "OCR_DEMO_ONLY",
            "message": "Student-card OCR only accepts synthetic or redacted demo images.",
            "redacted_text": "",
        }
    redacted = redact_student_card_text(visible_text or "姓名: 张三 学号: 202612340001 学校: CampusFlow大学")
    return {
        "verified": True,
        "error_code": None,
        "message": "Synthetic demo card fields are internally consistent.",
        "redacted_text": redacted,
    }

