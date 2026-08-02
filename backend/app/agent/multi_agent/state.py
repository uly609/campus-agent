from __future__ import annotations

from typing import Any, TypedDict


class MultiAgentState(TypedDict, total=False):
    request_id: str
    session_id: str
    user_id: str
    query: str
    max_turns: int
    turn_count: int
    message_hub: list[dict[str, Any]]
    artifacts: dict[str, Any]
    worker_results: list[dict[str, Any]]
    files: list[dict[str, str]]
    final_answer: str
    guardrail_flags: list[str]
    trace: list[dict[str, Any]]
    degraded_mode: list[str]


WORKER_NAMES = (
    "community_worker",
    "retrieval_worker",
    "multimodal_worker",
    "draft_worker",
    "eval_worker",
    "general_worker",
)

FINALIZE_NODE = "finalize_node"
