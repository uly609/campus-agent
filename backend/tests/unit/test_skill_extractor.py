from app.agent.skills.extractor import ProceduralSkillExtractor


def test_extractor_builds_evidence_backed_procedural_skill() -> None:
    skills = ProceduralSkillExtractor().extract(
        "版本发布流程：\n1. 执行回归测试\n2. 构建镜像\n3. 人工确认后发布",
        title="版本手册",
    )
    assert len(skills) == 1
    assert skills[0].steps == ("执行回归测试", "构建镜像", "人工确认后发布")
    assert "回归测试" in skills[0].evidence_quote
