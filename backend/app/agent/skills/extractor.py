from __future__ import annotations

import re

from app.agent.skills.registry import ProceduralSkill


class ProceduralSkillExtractor:
    """Extract small, evidence-backed SOP assets from governed documents.

    This deterministic extractor is the local fallback. A production provider
    can replace it with structured LLM extraction without changing the skill
    asset contract.
    """

    _heading = re.compile(
        r"(?m)^(?!\s*(?:\d+[.、)]|[-*]))\s*(?:#{1,6}\s*)?([^\n]{2,80})"
        r"\s*(?:流程|步骤|SOP|操作|排查|部署|发布|处理)\s*[:：]?",
        re.I,
    )
    _step = re.compile(r"(?:^|\n)\s*(?:\d+[.、)]|[-*])\s*(\S[^\n]{1,240})")

    def extract(self, text: str, *, title: str = "", max_skills: int = 5) -> list[ProceduralSkill]:
        body = str(text or "").strip()
        if not body or max_skills <= 0:
            return []
        matches = list(self._heading.finditer(body))
        skills: list[ProceduralSkill] = []
        if not matches:
            steps = [match.group(1).strip() for match in self._step.finditer(body)][:8]
            if steps:
                skills.append(
                    ProceduralSkill(
                        name=title or "未命名流程",
                        category="procedure",
                        summary=steps[0],
                        evidence_quote=steps[0],
                        steps=tuple(steps),
                        confidence=0.6,
                    )
                )
            return skills

        for index, match in enumerate(matches[:max_skills]):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
            section = body[start:end].strip()
            steps = [item.group(1).strip() for item in self._step.finditer(section)][:8]
            if not steps:
                continue
            name = match.group(1).strip() or title or f"流程 {index + 1}"
            skills.append(
                ProceduralSkill(
                    name=name,
                    category="procedure",
                    summary=steps[0],
                    evidence_quote=section[:240],
                    steps=tuple(steps),
                    confidence=0.75,
                )
            )
        return skills
