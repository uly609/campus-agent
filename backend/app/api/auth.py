from __future__ import annotations

from fastapi import Header, HTTPException

from app.core.config import get_settings


def require_demo_token(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {get_settings().demo_token}"
    if authorization is not None and authorization != expected:
        raise HTTPException(status_code=401, detail={"code": "INVALID_DEMO_TOKEN"})

