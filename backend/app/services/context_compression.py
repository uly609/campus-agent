from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.llm.base import ProviderRecoverableError
from app.llm.router import ProviderRouter
from app.services.repository import JsonRepository


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _message_text(message: dict[str, Any]) -> str:
    role = str(message.get("role", "user"))
    content = str(message.get("content", "")).strip()
    return f"{role}: {content}" if content else ""


def _estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


@dataclass(frozen=True)
class ContextWindow:
    summary: str
    summary_version: int
    compressed_through: int
    recent_messages: list[dict[str, Any]]
    estimated_tokens: int
    should_precompress: bool

    @property
    def virtual_context(self) -> str:
        parts: list[str] = []
        if self.summary:
            parts.append("[历史摘要]\n" + self.summary)
        if self.recent_messages:
            recent = "\n".join(
                row for row in (_message_text(item) for item in self.recent_messages) if row
            )
            parts.append("[最近对话]\n" + recent)
        return "\n\n".join(parts)


class ContextCompressionService:
    """Progressively compresses completed conversation turns without blocking chat."""

    _running: set[str] = set()

    def __init__(
        self,
        repo: JsonRepository | None = None,
        router: ProviderRouter | None = None,
    ) -> None:
        self.repo = repo or JsonRepository()
        self.router = router or ProviderRouter()
        settings = get_settings()
        self.enabled = settings.context_compression_enabled
        self.max_tokens = settings.context_max_tokens
        self.trigger_ratio = settings.context_trigger_ratio
        self.recent_limit = max(2, settings.context_recent_messages)

    def load_window(self, session_id: str, user_id: str) -> ContextWindow:
        messages = self.repo.load_chat_messages(session_id)
        snapshot = self.repo.load_context_snapshot(session_id) or {}
        compressed_through = min(int(snapshot.get("compressed_through", 0)), len(messages))
        recent_messages = messages[compressed_through:][-self.recent_limit :]
        text = "\n".join(_message_text(item) for item in messages)
        estimated_tokens = _estimate_tokens(text)
        threshold = int(self.max_tokens * self.trigger_ratio)
        should_precompress = (
            self.enabled
            and estimated_tokens >= threshold
            and len(messages) - compressed_through > self.recent_limit
        )
        return ContextWindow(
            summary=str(snapshot.get("summary", "")),
            summary_version=int(snapshot.get("version", 0)),
            compressed_through=compressed_through,
            recent_messages=recent_messages,
            estimated_tokens=estimated_tokens,
            should_precompress=should_precompress,
        )

    def schedule_precompression(self, session_id: str, user_id: str) -> bool:
        if not self.load_window(session_id, user_id).should_precompress:
            return False
        if session_id in self._running:
            return False
        self._running.add(session_id)
        task = asyncio.create_task(self.precompress(session_id, user_id))
        task.add_done_callback(lambda _: self._running.discard(session_id))
        return True

    async def precompress(self, session_id: str, user_id: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        messages = self.repo.load_chat_messages(session_id)
        old = self.repo.load_context_snapshot(session_id) or {}
        previous_cutoff = min(int(old.get("compressed_through", 0)), len(messages))
        cutoff = max(previous_cutoff, len(messages) - self.recent_limit)
        source_messages = messages[previous_cutoff:cutoff]
        if not source_messages:
            return old or None
        prompt = self._summary_prompt(str(old.get("summary", "")), source_messages)
        try:
            result = await self.router.chat(prompt)
            summary = self._normalize_summary(result.content)
            if not summary or result.degraded:
                raise ProviderRecoverableError("context summary provider degraded or returned invalid output")
        except (ProviderRecoverableError, ValueError, TypeError, json.JSONDecodeError):
            return old or None
        snapshot = {
            "snapshot_id": str(old.get("snapshot_id") or f"ctx-{uuid.uuid4().hex[:12]}"),
            "session_id": session_id,
            "user_id": user_id,
            "version": int(old.get("version", 0)) + 1,
            "summary": summary,
            "compressed_through": cutoff,
            "source_message_ids": [str(row.get("message_id", "")) for row in source_messages],
            "created_at": _now_iso(),
            "status": "committed",
        }
        return self.repo.save_context_snapshot(snapshot)

    @staticmethod
    def _summary_prompt(previous: str, messages: list[dict[str, Any]]) -> str:
        source = "\n".join(_message_text(item) for item in messages)
        return (
            "你是 Agent 会话上下文压缩器。请只输出 JSON，不要解释。\n"
            "把已完成对话压缩成可恢复的结构化摘要，保留用户约束、关键事实、工具结论、"
            "未完成事项和必要来源；不要把猜测写成事实。\n"
            '格式：{"completed_tasks":[],"constraints":[],"facts":[],"tool_conclusions":[],"open_items":[],"citations":[]}\n'
            f"旧摘要：{previous or '无'}\n本次待压缩消息：\n{source}"
        )

    @staticmethod
    def _normalize_summary(content: Any) -> str:
        if not isinstance(content, str):
            return ""
        value = content.strip()
        if value.startswith("```"):
            value = value.strip("`").removeprefix("json").strip()
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            return ""
        allowed = ("completed_tasks", "constraints", "facts", "tool_conclusions", "open_items", "citations")
        cleaned = {key: parsed.get(key, []) for key in allowed}
        if not any(cleaned.values()):
            return ""
        return json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))
