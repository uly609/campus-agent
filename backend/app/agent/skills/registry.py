from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AgentSkill:
    name: str
    description: str
    tools: tuple[str, ...]


class SkillRegistry:
    def __init__(self, skills: tuple[AgentSkill, ...] = ()) -> None:
        self._skills = {skill.name: skill for skill in skills}

    @property
    def skills(self) -> tuple[AgentSkill, ...]:
        return tuple(self._skills.values())

    @property
    def tool_names(self) -> frozenset[str]:
        return frozenset(tool for skill in self.skills for tool in skill.tools)

    def planner_catalog(self) -> list[dict[str, object]]:
        return [asdict(skill) for skill in self.skills]


DEFAULT_SKILLS = (
    AgentSkill(
        name="campus_knowledge",
        description="Answer campus policy, service, schedule and location questions with official evidence.",
        tools=("search_campus_docs", "get_campus_service_info", "search_official_web"),
    ),
    AgentSkill(
        name="community_search",
        description="Search campus community posts, events and lost-and-found records.",
        tools=("search_posts", "search_lost_and_found"),
    ),
    AgentSkill(
        name="post_creation",
        description="Create a campus post draft that must pass human review before publishing.",
        tools=("create_post_draft",),
    ),
    AgentSkill(
        name="memory_management",
        description="Load user-controlled memories to personalize planning without replacing official evidence.",
        tools=("load_user_memories",),
    ),
    AgentSkill(
        name="evaluation",
        description="Read the latest offline intent, retrieval and grounded-QA evaluation report.",
        tools=("get_eval_report",),
    ),
)


def default_skill_registry() -> SkillRegistry:
    return SkillRegistry(DEFAULT_SKILLS)
