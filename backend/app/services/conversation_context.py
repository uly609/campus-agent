from __future__ import annotations

import hashlib

from app.core.redis import get_redis_client


CONVERSATION_TTL_SECONDS = 2 * 60 * 60


def _context_key(user_id: str, session_id: str) -> str:
    identity = hashlib.sha256(f"{user_id}:{session_id}".encode()).hexdigest()
    return f"campusflow:conversation:last-query:{identity}"


def load_last_query(user_id: str, session_id: str) -> str:
    value = get_redis_client().get(_context_key(user_id, session_id))
    if isinstance(value, bytes):
        return value.decode()
    return str(value or "")


def save_last_query(user_id: str, session_id: str, query: str) -> None:
    get_redis_client().setex(
        _context_key(user_id, session_id),
        CONVERSATION_TTL_SECONDS,
        query,
    )


def clear_conversation_context(user_id: str, session_id: str) -> None:
    get_redis_client().delete(_context_key(user_id, session_id))
