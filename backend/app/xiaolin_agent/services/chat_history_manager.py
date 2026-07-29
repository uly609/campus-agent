from __future__ import annotations

import json
import logging
import uuid
from typing import Any, ClassVar

from app.domain.platform_schemas import UserSession
from app.services.repository import JsonRepository, now_iso
from app.xiaolin_agent.services.llm_service import LLMService, TOOL_LIBRARY_MODEL

logger = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: object) -> object:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()  # type: ignore[no-any-return,attr-defined]
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


class ChatHistoryManager:
    """XiaoLin chat history behavior using CampusFlow's persistent JSON store."""

    MAX_HISTORY_LENGTH = 10
    DEFAULT_TITLES: ClassVar[set[str | None]] = {"新的对话", "新对话", "", None}
    repo = JsonRepository()

    @classmethod
    async def get_chat_history(cls, session_id: str) -> list[dict[str, str]]:
        messages = cls.repo.load_xiaolin_messages(session_id)
        history = [
            {
                "role": "user" if bool(message.get("is_user")) else "assistant",
                "content": str(message.get("content", "")),
            }
            for message in messages
        ]
        return history[-cls.MAX_HISTORY_LENGTH * 2 :]

    @classmethod
    async def save_message(
        cls,
        session_id: str,
        user_id: str,
        content: str,
        is_user: bool,
    ) -> dict[str, Any]:
        message = {
            "id": f"msg-{uuid.uuid4().hex[:12]}",
            "content": content,
            "is_user": is_user,
            "created_at": now_iso(),
            "session_id": session_id,
        }
        cls.repo.save_xiaolin_message(message)
        sessions = cls.repo.load_sessions(user_id)
        session = next((item for item in sessions if item.session_id == session_id), None)
        if session is None:
            timestamp = now_iso()
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                title="新对话",
                created_at=timestamp,
                updated_at=timestamp,
            )
        session.message_count = len(cls.repo.load_xiaolin_messages(session_id))
        session.updated_at = now_iso()
        cls.repo.save_session(session)
        if not is_user:
            await cls.update_session_title_if_needed(session_id, user_id)
        return message

    @classmethod
    async def update_session_title_if_needed(cls, session_id: str, user_id: str) -> str | None:
        session = next(
            (item for item in cls.repo.load_sessions(user_id) if item.session_id == session_id),
            None,
        )
        if session is None or session.title not in cls.DEFAULT_TITLES:
            return session.title if session else None
        messages = cls.repo.load_xiaolin_messages(session_id)[:6]
        if not messages:
            return session.title
        title = await cls._generate_session_title(messages)
        if not title:
            first_user_message = next(
                (str(item.get("content", "")) for item in messages if item.get("is_user")),
                "",
            )
            title = cls._normalize_title(first_user_message)
        if title:
            session.title = title
            session.updated_at = now_iso()
            cls.repo.save_session(session)
        return session.title

    @classmethod
    async def _generate_session_title(cls, messages: list[dict[str, Any]]) -> str:
        conversation = "\n".join(
            f"{'用户' if item.get('is_user') else '助手'}: {cls._truncate_for_prompt(str(item.get('content', '')), 500)}"
            for item in messages
            if item.get("content")
        )
        prompt = f"""请根据下面这段聊天内容生成一个中文缩略标题。

要求：
1. 标题用于聊天历史列表，必须短小清楚。
2. 优先使用 4 到 10 个中文字符，最多不超过 16 个中文字符。
3. 不要使用引号、句号、冒号、前缀说明。
4. 不要输出“新对话”“聊天记录”等泛泛标题。

聊天内容：
{conversation}

只输出标题。"""
        try:
            llm = await LLMService.get_llm(model_name=TOOL_LIBRARY_MODEL, temperature=0.2)
            response = await llm.ainvoke([{"role": "user", "content": prompt}])
            return cls._normalize_title(str(response.content))
        except Exception:
            logger.warning("调用标题生成模型失败", exc_info=True)
            return ""

    @staticmethod
    def _truncate_for_prompt(text: str, max_length: int) -> str:
        text = (text or "").strip()
        return text if len(text) <= max_length else text[:max_length] + "..."

    @staticmethod
    def _normalize_title(title: str) -> str:
        title = (title or "").strip()
        title = title.strip("`\"'“”‘’《》<>（）()[]【】。、，,：:；;！!？? \n\t")
        title = " ".join(title.split())
        return title[:16]

    @classmethod
    async def save_process_info(
        cls,
        message_id: str,
        session_id: str,
        process_info: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "id": f"process-{uuid.uuid4().hex[:12]}",
            "message_id": message_id,
            "session_id": session_id,
            "created_at": now_iso(),
            "steps": process_info.get("steps", []),
            "task_plan": process_info.get("task_planning", {}),
            "tool_selections": process_info.get("tool_selection", {}),
            "task_results": process_info.get("task_execution", {}),
        }
        serialized = json.loads(json.dumps(payload, ensure_ascii=False, cls=CustomJSONEncoder))
        return cls.repo.save_xiaolin_process(serialized)
