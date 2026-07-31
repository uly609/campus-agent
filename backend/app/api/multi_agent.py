from __future__ import annotations

from fastapi import APIRouter

from app.agent.multi_agent.graph import MultiAgentGraph
from app.domain.platform_schemas import MultiAgentRequest, MultiAgentResponse

router = APIRouter(prefix="/api/v1")


@router.post("/agents/multi", response_model=MultiAgentResponse)
async def run_multi_agent_api(request: MultiAgentRequest) -> MultiAgentResponse:
    state = await MultiAgentGraph().run(
        request.query,
        request.session_id,
        request.user_id,
        request.max_turns,
        [item.model_dump() for item in request.files],
    )
    return MultiAgentResponse(
        request_id=str(state.get("request_id", "")),
        final_answer=str(state.get("final_answer", "")),
        worker_results=list(state.get("worker_results", [])),
        message_hub=list(state.get("message_hub", [])),
        turn_count=int(state.get("turn_count", 0)),
        trace=list(state.get("trace", [])),
        degraded_mode=list(state.get("degraded_mode", [])),
    )


@router.get("/agents/multi/spec")
def multi_agent_spec() -> dict[str, object]:
    return MultiAgentGraph().graph_spec()
