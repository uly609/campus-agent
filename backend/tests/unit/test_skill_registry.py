from __future__ import annotations

from app.agent.skills.registry import ProceduralSkill, SkillRegistry, default_skill_registry


def test_default_skill_registry_is_empty_until_governed_content_is_ingested() -> None:
    registry = default_skill_registry()
    assert registry.skills == ()


def test_skill_registry_stores_procedural_knowledge_assets_not_tools() -> None:
    registry = SkillRegistry()
    registry.add(
        ProceduralSkill(
            name="发布流程",
            category="release",
            steps=("执行测试", "发布镜像"),
            evidence_quote="发布流程：执行测试，再发布镜像。",
        )
    )
    assert registry.catalog()[0]["steps"] == ("执行测试", "发布镜像")
    assert registry.search("发布流程")[0].name == "发布流程"
