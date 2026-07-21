from __future__ import annotations

import re


def redact_pii(text: str) -> str:
    redacted = re.sub(r"\b1[3-9]\d{9}\b", "[REDACTED_PHONE]", text)
    redacted = re.sub(r"\b\d{8,18}\b", "[REDACTED_ID]", redacted)
    redacted = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", redacted)
    return redacted


def contains_sensitive_memory(text: str) -> bool:
    return redact_pii(text) != text or any(word in text for word in ["密码", "身份证", "手机号", "银行卡"])

