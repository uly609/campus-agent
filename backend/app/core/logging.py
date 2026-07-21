from __future__ import annotations

import logging
import re
from typing import Any

SECRET_PATTERNS = [
    re.compile(r"(sk-[A-Za-z0-9_-]{12,})"),
    re.compile(r"(\d{6,})"),
]


class PrivacyFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in SECRET_PATTERNS:
            message = pattern.sub("[REDACTED]", message)
        record.msg = message
        record.args = ()
        return True


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger().addFilter(PrivacyFilter())


def safe_extra(**values: Any) -> dict[str, Any]:
    return {key: "[REDACTED]" if "secret" in key or "key" in key else value for key, value in values.items()}

