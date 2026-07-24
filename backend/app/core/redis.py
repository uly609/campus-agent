git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
from __future__ import annotations

import time
from typing import Any, Optional

from app.core.config import get_settings


class InMemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expirations: dict[str, float] = {}
        self.streams: dict[str, list[dict[str, Any]]] = {}

    def setex(self, key: str, seconds: int, value: str) -> bool:
        self.values[key] = value
        self.expirations[key] = time.monotonic() + seconds
        return True

    def get(self, key: str) -> Optional[str]:
        if key in self.expirations and self.expirations[key] <= time.monotonic():
            self.delete(key)
            return None
        return self.values.get(key)

    def incr(self, key: str) -> int:
        value = int(self.get(key) or "0") + 1
        self.values[key] = str(value)
        return value

    def expire(self, key: str, seconds: int) -> bool:
        if key not in self.values:
            return False
        self.expirations[key] = time.monotonic() + seconds
        return True

    def xadd(self, stream: str, fields: dict[str, Any], maxlen: int | None = None, approximate: bool = True) -> str:
        entry_id = f"{len(self.streams.get(stream, [])) + 1}-0"
        self.streams.setdefault(stream, []).append({"id": entry_id, "fields": fields})
        if maxlen and len(self.streams[stream]) > maxlen:
            self.streams[stream] = self.streams[stream][-maxlen:]
        return entry_id

    def xrange(self, stream: str) -> list[tuple[str, dict[str, Any]]]:
        return [(entry["id"], entry["fields"]) for entry in self.streams.get(stream, [])]

    def delete(self, key: str) -> int:
        existed = key in self.values
        self.values.pop(key, None)
        self.expirations.pop(key, None)
        return int(existed)


_fallback = InMemoryRedis()


def get_redis_client() -> Any:
    try:
        import redis
    except ImportError:
        return _fallback

    try:
        client = redis.Redis.from_url(get_settings().redis_url, decode_responses=True, socket_timeout=1)
        client.ping()
        return client
    except (OSError, TimeoutError, ValueError, redis.exceptions.RedisError):
        return _fallback
