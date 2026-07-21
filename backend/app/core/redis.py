from __future__ import annotations

from typing import Any, Optional

from app.core.config import get_settings


class InMemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.streams: dict[str, list[dict[str, Any]]] = {}

    def setex(self, key: str, seconds: int, value: str) -> bool:
        self.values[key] = value
        return True

    def get(self, key: str) -> Optional[str]:
        return self.values.get(key)

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
        return int(existed)


_fallback = InMemoryRedis()


def get_redis_client() -> Any:
    try:
        import redis

        client = redis.Redis.from_url(get_settings().redis_url, decode_responses=True, socket_timeout=1)
        client.ping()
        return client
    except (ImportError, OSError, TimeoutError, ValueError):
        return _fallback

