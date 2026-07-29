from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter

from app.xiaolin_agent.services.llm_service import MAIN_AGENT_MODEL, TOOL_LIBRARY_MODEL

router = APIRouter(prefix="/api")


@router.get("/llm/config-status/")
async def llm_config_status() -> dict[str, Any]:
    providers = [
        {
            "name": "DeepSeek",
            "env": "DEEPSEEK_API_KEY",
            "configured": bool(os.getenv("DEEPSEEK_API_KEY")),
            "model": f"{MAIN_AGENT_MODEL} / {TOOL_LIBRARY_MODEL}",
        },
        {
            "name": "智谱 GLM",
            "env": "GLM_API_KEY",
            "configured": bool(os.getenv("GLM_API_KEY")),
            "model": "glm-4-flash",
        },
    ]
    return {
        "status": "success",
        "data": {
            "configured": any(bool(provider["configured"]) for provider in providers),
            "providers": providers,
            "env_file": ".env",
        },
    }
