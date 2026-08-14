from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.core.config import get_settings
MAIN_AGENT_MODEL = "qwen-plus"
TOOL_LIBRARY_MODEL = "qwen-turbo"

router = APIRouter(prefix="/api")


@router.get("/llm/config-status/")
async def llm_config_status() -> dict[str, Any]:
    settings = get_settings()
    aliyun_configured = bool(settings.bailian_api_key)
    roles = {
        "chat": {
            "configured": bool(settings.cloud_fallback_chat_url and settings.bailian_api_key),
            "model": settings.cloud_fallback_chat_model,
        },
        "embedding": {
            "configured": bool(settings.cloud_fallback_embedding_url and settings.bailian_api_key),
            "model": settings.cloud_fallback_embedding_model,
        },
        "vision": {
            "configured": bool(
                settings.cloud_fallback_vlm_url
                and (settings.vlm_api_key or settings.bailian_api_key)
            ),
            "model": settings.cloud_fallback_vlm_model,
        },
    }
    providers = [
        {
            "name": "阿里云百炼",
            "env": "DASHSCOPE_API_KEY",
            "configured": aliyun_configured,
            "model": f"{MAIN_AGENT_MODEL} / {TOOL_LIBRARY_MODEL}",
            "roles": roles,
        }
    ]
    return {
        "status": "success",
        "data": {
            "configured": aliyun_configured,
            "active_provider": "阿里云百炼" if aliyun_configured else None,
            "roles": roles,
            "providers": providers,
            "env_file": ".env",
        },
    }
