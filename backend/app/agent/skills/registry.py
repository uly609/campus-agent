from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ProceduralSkill:
    """A reusable SOP extracted from governed enterprise content.

    Skills are knowledge assets, not another tool-routing layer. A skill records
    the procedure, its evidence, and the inputs/outputs needed to reuse it.
    """

    name: str
    category: str = ""
    summary: str = ""
    evidence_quote: str = ""
    steps: tuple[str, ...] = field(default_factory=tuple)
    inputs: tuple[str, ...] = field(default_factory=tuple)
    outputs: tuple[str, ...] = field(default_factory=tuple)
    tools: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0


# Compatibility alias for callers that imported the old name. The object now
# represents a procedural knowledge asset rather than a business tool bundle.
AgentSkill = ProceduralSkill


class SkillRegistry:
    def __init__(self, skills: tuple[ProceduralSkill, ...] = ()) -> None:
        self._skills = {skill.name: skill for skill in skills}

    @property
    def skills(self) -> tuple[AgentSkill, ...]:
        return tuple(self._skills.values())

    def add(self, skill: ProceduralSkill) -> None:
        self._skills[skill.name] = skill

    def search(self, query: str, limit: int = 5) -> tuple[ProceduralSkill, ...]:
        terms = {part.casefold() for part in query.split() if part.strip()}
        ranked = sorted(
            self.skills,
            key=lambda skill: sum(
                term in f"{skill.name} {skill.summary} {' '.join(skill.tags)}".casefold()
                for term in terms
            ),
            reverse=True,
        )
        return tuple(ranked[: max(0, limit)])

    def catalog(self) -> list[dict[str, object]]:
        return [asdict(skill) for skill in self.skills]


def default_skill_registry() -> SkillRegistry:
    # Skills are populated from approved documents during ingestion. Keeping
    # this empty prevents the planner from confusing SOP assets with tools.
    return SkillRegistry()
