from __future__ import annotations

from app.agent.planner import StructuredPlanner
from app.domain.enums import Intent


def plan_intent(query: str, user_id: str) -> tuple[Intent, list[dict[str, object]], float]:
    """Compatibility adapter for callers that still consume the legacy tuple plan."""
    plan = StructuredPlanner().fallback_plan(query, user_id)
    return plan.intent, plan.to_steps(), plan.confidence
