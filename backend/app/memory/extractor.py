from __future__ import annotations

import hashlib
import uuid

from app.domain.enums import MemoryType
from app.domain.schemas import MemoryRecord
from app.retrieval.embeddings import embed_text
from app.security.pii import contains_sensitive_memory
from app.services.repository import now_iso


def normalize_key(text: str) -> str:
    if "喜欢" in text or "偏好" in text:
        return "preference"
    if "下周" in text or "明天" in text or "周" in text:
        return "event"
    return "fact"


def extract_memories(user_id: str, text: str) -> list[MemoryRecord]:
    if contains_sensitive_memory(text):
        return []
    if not any(marker in text for marker in ["记住", "我喜欢", "我的", "下周", "偏好"]):
        return []
    key = normalize_key(text)
    memory_type = MemoryType.PREFERENCE if key == "preference" else MemoryType.EVENT if key == "event" else MemoryType.FACT
    clean_value = text.replace("记住", "").strip(" ：:")
    hash_value = hashlib.sha256(f"{user_id}:{key}:{clean_value}".encode("utf-8")).hexdigest()
    return [
        MemoryRecord(
            memory_id=f"mem-{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            memory_type=memory_type,
            key=key,
            value=clean_value,
            hash_value=hash_value,
            embedding=embed_text(clean_value)[:32],
            supersedes=None,
            expires_at=None,
            created_at=now_iso(),
        )
    ]

