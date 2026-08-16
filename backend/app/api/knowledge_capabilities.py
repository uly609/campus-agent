from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge-community"])


@router.get("/capabilities")
def capabilities() -> dict[str, object]:
    return {
        "product": "AtlasHub AI",
        "domain": "enterprise_knowledge_community",
        "skills": {
            "kind": "procedural_knowledge_assets",
            "description": "由受治理文档抽取的 SOP、步骤、输入、输出和证据引用。",
            "extractor": "ProceduralSkillExtractor",
        },
        "tools": [
            "search_knowledge_base",
            "get_knowledge_service_info",
            "search_posts",
            "get_post_detail",
            "search_lost_and_found",
            "search_official_web",
            "analyze_post_image",
            "create_post_draft",
            "load_user_memories",
            "save_memory_feedback",
            "get_eval_report",
        ],
        "safety": {"draft_requires_confirmation": True, "external_content_is_untrusted": True},
    }
