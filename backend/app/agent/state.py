from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    request_id: str
    session_id: str
    user_id: str
    raw_query: str
    resolved_query: str
    image_urls: list[str]
    image_context: list[dict[str, Any]]
    conversation_summary: str
    memory_context: list[dict[str, Any]]
    intent: str
    intent_confidence: float
    plan: list[dict[str, Any]]
    current_step: int
    tool_results: list[dict[str, Any]]
    retrieved_evidence: list[dict[str, Any]]
    relevance_score: float
    evidence_coverage: float
    replan_count: int
    max_replans: int
    citations: list[dict[str, Any]]
    final_answer: str
    guardrail_flags: list[str]
    errors: list[dict[str, Any]]
    trace: list[dict[str, Any]]
    degraded_mode: list[str]


REQUIRED_NODES = [
    "input_guard_node",
    "load_memory_node",
    "coreference_resolver_node",
    "visual_understanding_node",
    "intent_planner_node",
    "tool_executor_node",
    "retrieval_gate_node",
    "relevance_judge_node",
    "replan_node",
    "grounded_synthesis_node",
    "output_guard_node",
    "publish_memory_event_node",
    "persist_trace_node",
]

SIX_STAGES = [
    "coreference_resolution",
    "visual_understanding",
    "intent_planning",
    "tool_execution",
    "relevance_gate_and_replan",
    "grounded_synthesis",
]

