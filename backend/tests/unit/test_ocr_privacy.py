from __future__ import annotations

from app.multimodal.ocr import verify_demo_student_card
from app.multimodal.privacy import redact_student_card_text


def test_student_card_ocr_is_demo_only() -> None:
    real = verify_demo_student_card("real-upload.png", "姓名: 张三 学号: 202612340001")
    assert real["verified"] is False
    demo = verify_demo_student_card("synthetic-card.png", "姓名: 张三 学号: 202612340001")
    assert demo["verified"] is True
    assert "202612340001" not in demo["redacted_text"]


def test_redacts_student_identity_text() -> None:
    assert "[REDACTED_STUDENT_ID]" in redact_student_card_text("学号: 202612340001")

