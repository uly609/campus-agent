from __future__ import annotations

from app.agent.planner.schemas import IntentPlan


class PlanValidationError(ValueError):
    pass


class PlanValidator:
    _required_arguments: dict[str, frozenset[str]] = {
        "search_campus_docs": frozenset({"query"}),
        "search_posts": frozenset({"query"}),
        "search_lost_and_found": frozenset({"query"}),
        "get_campus_service_info": frozenset({"query"}),
        "create_post_draft": frozenset({"intent"}),
        "load_user_memories": frozenset({"user_id"}),
    }

    def __init__(self, registered_tools: frozenset[str] | set[str]) -> None:
        self.registered_tools = frozenset(registered_tools)

    def validate(self, plan: IntentPlan) -> IntentPlan:
        for call in plan.tool_calls:
            if call.tool_name not in self.registered_tools:
                raise PlanValidationError(f"tool is not registered: {call.tool_name}")
            missing = self._required_arguments.get(call.tool_name, frozenset()) - call.arguments.keys()
            if missing:
                names = ", ".join(sorted(missing))
                raise PlanValidationError(f"{call.tool_name} is missing required arguments: {names}")
        return plan
