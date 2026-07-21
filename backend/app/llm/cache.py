from __future__ import annotations

import hashlib
import json
from typing import Any

from app.core.config import get_settings
from app.core.redis import get_redis_client


class ExactMatchCache:
    def __init__(self) -> None:
        self.client = get_redis_client()

    def key(self, role: str, provider: str, model: str, payload: Any) -> str:
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return f"campusflow:llm:{role}:{provider}:{model}:{get_settings().prompt_version}:{digest}"

    def get(self, key: str) -> Any | None:
        value = self.client.get(key)
        if value is None:
            return None
        return json.loads(value)

    def set(self, key: str, value: Any, seconds: int = 900) -> None:
        serialized = json.dumps(value, ensure_ascii=False)
        self.client.setex(key, seconds, serialized)
