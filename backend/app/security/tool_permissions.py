from __future__ import annotations

ALLOWED_TOOLS = {
    "search_campus_docs",
    "search_posts",
    "get_post_detail",
    "search_lost_and_found",
    "get_campus_events",
    "get_campus_service_info",
    "analyze_post_image",
    "verify_demo_student_card",
    "create_post_draft",
    "load_user_memories",
    "save_memory_feedback",
}


def assert_tool_allowed(tool_name: str) -> None:
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError(f"TOOL_NOT_ALLOWED:{tool_name}")

