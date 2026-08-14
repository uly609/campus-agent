from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge-community"])


@router.get("/capabilities")
def capabilities() -> dict[str, object]:
    return {
        "product": "AtlasHub AI",
        "domain": "enterprise_knowledge_community",
        "skills": [
            {"name": "enterprise_knowledge", "tool": "search_knowledge_base"},
            {"name": "community_search", "tool": "search_posts"},
            {"name": "multimodal_documents", "tool": "parse_document_file"},
            {"name": "content_governance", "tool": "create_post_draft"},
            {"name": "evaluation", "tool": "get_eval_report"},
        ],
        "safety": {"draft_requires_confirmation": True, "external_content_is_untrusted": True},
    }
