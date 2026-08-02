from __future__ import annotations

import uuid
from typing import Any, Callable

from langgraph.graph import END, START, StateGraph

from app.agent.multi_agent.state import FINALIZE_NODE, MultiAgentState, WORKER_NAMES
from app.agent.multi_agent.supervisor import MultiAgentSupervisor
from app.agent.multi_agent.workers import MultiAgentWorkers
from app.llm.router import ProviderRouter
from app.services.repository import JsonRepository


class MultiAgentGraph:
    def __init__(self, repo: JsonRepository | None = None, router: ProviderRouter | None = None) -> None:
        self.repo = repo or JsonRepository()
        self.router = router or ProviderRouter()
        self.supervisor = MultiAgentSupervisor()
        self.workers = MultiAgentWorkers(self.repo, self.router)
        self.compiled = self._compile()

    def _worker_runner(self, name: str) -> Callable[[MultiAgentState], Any]:
        async def run_node(state: MultiAgentState) -> MultiAgentState:
            await getattr(self.workers, name)(state)
            return state

        return run_node

    def _compile(self) -> Any:
        workflow = StateGraph(MultiAgentState)
        workflow.add_node("supervisor_node", self.supervisor.supervise)
        for name in WORKER_NAMES:
            workflow.add_node(name, self._worker_runner(name))
        workflow.add_node(FINALIZE_NODE, self.finalize_node)
        workflow.add_edge(START, "supervisor_node")
        route_map: dict[Any, str] = {name: name for name in (*WORKER_NAMES, FINALIZE_NODE)}
        workflow.add_conditional_edges("supervisor_node", self.supervisor.route, route_map)
        for name in WORKER_NAMES:
            workflow.add_edge(name, "supervisor_node")
        workflow.add_edge(FINALIZE_NODE, END)
        return workflow.compile()

    async def finalize_node(self, state: MultiAgentState) -> MultiAgentState:
        if not state.get("final_answer"):
            campus = state.get("artifacts", {}).get("campus_worker", {})
            answer_parts: list[str] = []
            campus_answer = str(campus.get("answer", "")).strip()
            if campus_answer:
                answer_parts.append(campus_answer)
            community = state.get("artifacts", {}).get("community_worker", {})
            community_posts = community.get("posts", [])
            if community_posts:
                lines = [
                    f"{index}. {item.get('title', '')}（{item.get('category', '')}，"
                    f"{item.get('like_count', 0)} 赞 / {item.get('comment_count', 0)} 评论）"
                    for index, item in enumerate(community_posts[:5], start=1)
                ]
                answer_parts.append("校园社区推荐：\n" + "\n".join(lines))
            multimodal = state.get("artifacts", {}).get("multimodal_worker", {})
            chunks = multimodal.get("chunks", [])
            if chunks:
                previews = [str(item.get("text", ""))[:240] for item in chunks[:3]]
                answer_parts.append("附件解析结果：\n" + "\n".join(previews))
            draft = state.get("artifacts", {}).get("draft_worker", {})
            if draft.get("draft"):
                answer_parts.append("帖子草稿：\n" + str(draft["draft"]))
            evaluation = state.get("artifacts", {}).get("eval_worker", {})
            if evaluation.get("summary"):
                answer_parts.append(str(evaluation["summary"]))
            general = state.get("artifacts", {}).get("general_worker", {})
            if general.get("answer"):
                answer_parts.append(str(general["answer"]))
            answer = "\n\n".join(part for part in answer_parts if part).strip()
            if not answer:
                evidence = state.get("artifacts", {}).get("retrieval_worker", {}).get("evidence", [])
                if evidence:
                    lines = [
                        f"{index}. 《{item.get('title', '')}》 {item.get('excerpt', '')[:180]}"
                        f"（来源：{item.get('source_id', '')}）"
                        for index, item in enumerate(evidence[:3], start=1)
                    ]
                    answer = "根据校园知识检索结果：\n" + "\n".join(lines)
                else:
                    answer = (
                        "多 Agent 协作已完成。该问题需要更具体的校园数据或附件，"
                        "请提供文件或改用 Agent 查询。"
                    )
            state["final_answer"] = answer
        state["trace"].append(
            {
                "event": "multi_agent_finalized",
                "turn_count": state.get("turn_count", 0),
                "workers": [str(item.get("worker")) for item in state.get("worker_results", [])],
            }
        )
        return state

    async def run(
        self,
        query: str,
        session_id: str,
        user_id: str,
        max_turns: int = 4,
        files: list[dict[str, str]] | None = None,
        chat_history: list[dict[str, str]] | None = None,
    ) -> MultiAgentState:
        state: MultiAgentState = {
            "request_id": f"ma-{uuid.uuid4().hex[:12]}",
            "session_id": session_id,
            "user_id": user_id,
            "query": query,
            "max_turns": max_turns,
            "turn_count": 0,
            "complexity": "single",
            "required_workers": [],
            "task_completed": False,
            "message_hub": [],
            "artifacts": {},
            "worker_results": [],
            "files": files or [],
            "chat_history": chat_history or [],
            "final_answer": "",
            "guardrail_flags": [],
            "trace": [],
            "degraded_mode": [],
        }
        return await self.compiled.ainvoke(state)

    def graph_spec(self) -> dict[str, object]:
        return {
            "framework": "LangGraph StateGraph",
            "pattern": "supervisor_workers",
            "supervisor": "supervisor_node",
            "workers": list(WORKER_NAMES),
            "shared_state": ["required_workers", "message_hub", "artifacts", "worker_results"],
            "max_turns": 4,
            "guardrails": ["prompt_injection", "worker_whitelist", "required_worker_limit"],
            "communication": "message_hub publish + artifacts shared blackboard",
            "termination": "all required workers completed or max_turns reached",
        }


async def run_multi_agent(
    query: str,
    session_id: str,
    user_id: str,
    max_turns: int = 4,
    files: list[dict[str, str]] | None = None,
    chat_history: list[dict[str, str]] | None = None,
) -> MultiAgentState:
    return await MultiAgentGraph().run(query, session_id, user_id, max_turns, files, chat_history)
