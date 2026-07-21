from __future__ import annotations

import pytest

from app.agent.graph import build_graph, run_agent
from app.agent.state import REQUIRED_NODES, SIX_STAGES


def test_graph_preserves_required_nodes_and_stages() -> None:
    spec = build_graph().graph_spec()
    assert spec["nodes"] == REQUIRED_NODES
    assert spec["stages"] == SIX_STAGES
    assert spec["max_replans"] == 2


@pytest.mark.asyncio
async def test_replan_never_exceeds_two() -> None:
    state = await run_agent("火星校区的飞船停车费是多少？", "s1", "u1")
    assert state["replan_count"] <= 2

