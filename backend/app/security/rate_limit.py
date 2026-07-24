from __future__ import annotations

import hashlib
import time
from typing import Any

from fastapi import Request

from app.core.config import get_settings
from app.core.redis import get_redis_client


class RateLimiter:
    def __init__(self, redis_client: Any | None = None) -> None:
        self.redis = redis_client or get_redis_client()

    def check(self, request: Request) -> tuple[bool, int, int, int]:
        settings = get_settings()
        limit = (
            settings.chat_rate_limit_per_minute
            if request.url.path == "/api/v1/chat"
            else settings.api_rate_limit_per_minute
        )
        identity = request.headers.get("x-user-id") or (
            request.client.host if request.client else "anonymous"
        )
        identity_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
        window = int(time.time() // 60)
        key = f"campusflow:rate:{identity_hash}:{request.url.path}:{window}"
        count = int(self.redis.incr(key))
        if count == 1:
            self.redis.expire(key, 61)
        remaining = max(limit - count, 0)
        reset = (window + 1) * 60
        return count <= limit, limit, remaining, reset
