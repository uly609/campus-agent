from __future__ import annotations

from app.agent.skills.registry import default_skill_registry


def test_default_skills_expose_only_registered_planner_tools() -> None:
    registry = default_skill_registry()
    names = {skill.name for skill in registry.skills}
    assert names == {
        "enterprise_knowledge",
        "community_search",
        "post_creation",
        "memory_management",
        "evaluation",
    }
    assert "search_official_web" in registry.tool_names
    assert "search_knowledge_base" in registry.tool_names
    assert all(skill.description and skill.tools for skill in registry.skills)
