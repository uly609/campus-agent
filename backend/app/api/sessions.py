from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domain.platform_schemas import UserSession
from app.services.repository import JsonRepository, now_iso

router = APIRouter(prefix="/api/v1/sessions")
repo = JsonRepository()


class SessionCreate(BaseModel):
    user_id: str = Field(default="demo-user", min_length=1, max_length=120)
    title: str = Field(default="新对话", min_length=1, max_length=80)


@router.get("", response_model=list[UserSession])
def list_sessions(user_id: str = "demo-user") -> list[UserSession]:
    return sorted(repo.load_sessions(user_id), key=lambda item: item.updated_at, reverse=True)


@router.post("", response_model=UserSession)
def create_session(payload: SessionCreate) -> UserSession:
    timestamp = now_iso()
    return repo.save_session(
        UserSession(
            session_id=f"session-{uuid.uuid4().hex[:12]}",
            user_id=payload.user_id,
            title=payload.title,
            created_at=timestamp,
            updated_at=timestamp,
        )
    )


@router.delete("/{session_id}")
def delete_session(session_id: str, user_id: str = "demo-user") -> dict[str, object]:
    if not repo.delete_session(user_id, session_id):
        raise HTTPException(status_code=404, detail={"code": "SESSION_NOT_FOUND"})
    return {"deleted": True, "session_id": session_id}
