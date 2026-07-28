from __future__ import annotations

import time
import uuid
from typing import Any, Awaitable, Callable, Literal

from langgraph.graph import END, START, StateGraph

from app.agent.grounded_llm import synthesize_with_provider
from app.agent.planner import PlanValidator, StructuredPlanner
from app.agent.policies import judge_relevance, synthesize_grounded_answer
from app.agent.state import AgentState, REQUIRED_NODES, SIX_STAGES
from app.agent.tools.campus_tools import build_registry
from app.domain.enums import Intent
from app.domain.schemas import Citation, Evidence, MemoryRecord
from app.memory.producer import publish_memory_event
from app.memory.recall import recall_relevant_memories
from app.llm.base import ProviderRecoverableError
from app.llm.router import ProviderRouter
from app.multimodal.image_attributes import enhance_query_with_image
from app.security.pii import redact_pii
from app.security.prompt_injection import detect_prompt_injection, isolate_untrusted_content
from app.services.repository import JsonRepository


NodeCallable = Callable[[AgentState], Any]
GraphRoute = Literal[
    "visual_understanding_node",
    "intent_planner_node",
    "tool_executor_node",
    "grounded_synthesis_node",
    "replan_node",
]


class CampusFlowGraph:
    def __init__(self, repo: JsonRepository | None = None) -> None:
        self.repo = repo or JsonRepository()
        self.provider_router = ProviderRouter()
        self.registry = build_registry()
        self.planner = StructuredPlanner(
            PlanValidator(self.registry.tool_names), self.provider_router
        )
        self.nodes = {
            "input_guard_node": self.input_guard_node,
            "load_memory_node": self.load_memory_node,
            "coreference_resolver_node": self.coreference_resolver_node,
            "visual_understanding_node": self.visual_understanding_node,
            "intent_planner_node": self.intent_planner_node,
            "tool_executor_node": self.tool_executor_node,
            "retrieval_gate_node": self.retrieval_gate_node,
            "relevance_judge_node": self.relevance_judge_node,
            "replan_node": self.replan_node,
            "grounded_synthesis_node": self.grounded_synthesis_node,
            "output_guard_node": self.output_guard_node,
            "publish_memory_event_node": self.publish_memory_event_node,
            "persist_trace_node": self.persist_trace_node,
        }
        self.compiled = self._compile()

    def _compile(self) -> Any:
        workflow = StateGraph(AgentState)
        for name in REQUIRED_NODES:
            workflow.add_node(name, self._node_runner(name))

        workflow.add_edge(START, "input_guard_node")
        workflow.add_edge("input_guard_node", "load_memory_node")
        workflow.add_edge("load_memory_node", "coreference_resolver_node")
        workflow.add_conditional_edges("coreference_resolver_node", self._route_visual)
        workflow.add_edge("visual_understanding_node", "intent_planner_node")
        workflow.add_conditional_edges("intent_planner_node", self._route_intent)
        workflow.add_edge("tool_executor_node", "retrieval_gate_node")
        workflow.add_edge("retrieval_gate_node", "relevance_judge_node")
        workflow.add_conditional_edges("relevance_judge_node", self._route_relevance)
        workflow.add_edge("replan_node", "tool_executor_node")
        workflow.add_edge("grounded_synthesis_node", "output_guard_node")
        workflow.add_edge("output_guard_node", "publish_memory_event_node")
        workflow.add_edge("publish_memory_event_node", "persist_trace_node")
        workflow.add_edge("persist_trace_node", END)
        return workflow.compile()

    def _node_runner(self, name: str) -> Callable[[AgentState], Awaitable[AgentState]]:
        async def run_node(state: AgentState) -> AgentState:
            await self._run_node(name, state)
            return state

        return run_node

    @staticmethod
    def _route_visual(state: AgentState) -> GraphRoute:
        return "visual_understanding_node" if state.get("image_urls") else "intent_planner_node"

    @staticmethod
    def _route_intent(state: AgentState) -> GraphRoute:
        return (
            "grounded_synthesis_node"
            if state.get("intent") == Intent.GREETING.value
            else "tool_executor_node"
        )

    @staticmethod
    def _route_relevance(state: AgentState) -> GraphRoute:
        if any(
            result.get("tool_name") == "create_venue_reservation_draft"
            and result.get("success")
            for result in state.get("tool_results", [])
        ):
            return "grounded_synthesis_node"
        if state.get("evidence_coverage", 0.0) >= 0.25:
            return "grounded_synthesis_node"
        if state.get("replan_count", 0) >= state.get("max_replans", 2):
            return "grounded_synthesis_node"
        return "replan_node"

    def graph_spec(self) -> dict[str, object]:
        return {
            "framework": "LangGraph StateGraph",
            "stages": SIX_STAGES,
            "nodes": REQUIRED_NODES,
            "edges": [
                ("input_guard_node", "load_memory_node"),
                ("load_memory_node", "coreference_resolver_node"),
                ("coreference_resolver_node", "visual_understanding_node", "if image_urls"),
                ("coreference_resolver_node", "intent_planner_node", "if no image_urls"),
                ("visual_understanding_node", "intent_planner_node"),
                ("intent_planner_node", "grounded_synthesis_node", "if greeting"),
                ("intent_planner_node", "tool_executor_node", "if tool required"),
                ("tool_executor_node", "retrieval_gate_node"),
                ("retrieval_gate_node", "relevance_judge_node"),
                ("relevance_judge_node", "replan_node", "if insufficient and replan_count < 2"),
                ("replan_node", "tool_executor_node"),
                ("relevance_judge_node", "grounded_synthesis_node", "if sufficient or max replans"),
                ("grounded_synthesis_node", "output_guard_node"),
                ("output_guard_node", "publish_memory_event_node"),
                ("publish_memory_event_node", "persist_trace_node"),
            ],
            "max_replans": 2,
        }

    async def run(
        self,
        raw_query: str,
        session_id: str,
        user_id: str,
        image_urls: list[str] | None = None,
        conversation_summary: str = "",
    ) -> AgentState:
        state: AgentState = {
            "request_id": f"req-{uuid.uuid4().hex[:12]}",
            "session_id": session_id,
            "user_id": user_id,
            "raw_query": raw_query,
            "image_urls": image_urls or [],
            "image_context": [],
            "conversation_summary": conversation_summary,
            "memory_context": [],
            "tool_results": [],
            "retrieved_evidence": [],
            "replan_count": 0,
            "max_replans": 2,
            "citations": [],
            "guardrail_flags": [],
            "errors": [],
            "trace": [],
            "degraded_mode": self.provider_router.degraded_modes,
        }
        result = await self.compiled.ainvoke(state)
        return AgentState(**result)

    async def _run_node(self, name: str, state: AgentState) -> None:
        start = time.perf_counter()
        state.setdefault("trace", []).append({"event": "node_started", "node": name})
        await self.nodes[name](state)
        latency_ms = int((time.perf_counter() - start) * 1000)
        state["trace"].append({"event": "node_finished", "node": name, "latency_ms": latency_ms})

    async def input_guard_node(self, state: AgentState) -> None:
        flags = detect_prompt_injection(state["raw_query"])
        if flags:
            state.setdefault("guardrail_flags", []).extend(["input_prompt_injection"])
        state["raw_query"] = redact_pii(state["raw_query"])

    async def load_memory_node(self, state: AgentState) -> None:
        result = await self.registry.call("load_user_memories", {"user_id": state["user_id"]})
        memories = list(result.data or [])
        query = state.get("raw_query", "")
        relevant_memories = recall_relevant_memories(
            query, [MemoryRecord.model_validate(item) for item in memories]
        )
        state["memory_context"] = relevant_memories
        state["tool_results"].append(result.model_dump())
        state["trace"].append(
            {
                "event": "memory_recall",
                "candidate_count": len(memories),
                "used_count": len(relevant_memories),
                "reason": "query_related_only",
            }
        )

    async def coreference_resolver_node(self, state: AgentState) -> None:
        query = state["raw_query"]
        summary = state.get("conversation_summary", "")
        if summary and self._is_followup(query):
            query = self._resolve_followup(query, summary)
            state["trace"].append({"event": "coreference_resolved"})
        state["resolved_query"] = query

    @staticmethod
    def _is_followup(query: str) -> bool:
        normalized = query.strip("？?。！! ")
        markers = ("那", "它", "这个", "那里", "呢", "周末", "节假日", "然后")
        return len(normalized) <= 24 and any(marker in normalized for marker in markers)

    @staticmethod
    def _resolve_followup(query: str, previous_query: str) -> str:
        topics = (
            "图书馆",
            "食堂",
            "校园卡",
            "宿舍",
            "校园网",
            "体育馆",
            "快递",
            "校车",
            "心理咨询",
            "选课",
            "考试",
        )
        topic = next((item for item in topics if item in previous_query), "")
        if not topic:
            return f"{previous_query}；继续追问：{query}"
        if "周末" in query or "节假日" in query:
            return f"{topic} 周末 节假日 开放时间 安排"
        if any(marker in query for marker in ("哪里", "哪儿", "那里", "在哪")):
            return f"{topic} 地点 在哪里"
        if any(marker in query for marker in ("几点", "时间", "什么时候")):
            return f"{topic} 开放时间 {query}"
        return f"{topic} {query}"

    async def visual_understanding_node(self, state: AgentState) -> None:
        contexts = []
        for image_url in state.get("image_urls", []):
            result = await self.registry.call("analyze_post_image", {"image_url": image_url})
            if result.success and isinstance(result.data, dict):
                contexts.append(result.data)
            state["tool_results"].append(result.model_dump())
        state["image_context"] = contexts
        if contexts:
            state["resolved_query"] = enhance_query_with_image(state["resolved_query"], contexts[0])

    async def intent_planner_node(self, state: AgentState) -> None:
        query = state["resolved_query"]
        plan = await self.planner.plan(query, state["user_id"], state.get("memory_context", []))
        state["intent"] = plan.intent.value
        state["intent_confidence"] = plan.confidence
        state["plan"] = plan.to_steps()
        state["current_step"] = 0

    async def tool_executor_node(self, state: AgentState) -> None:
        evidence: list[dict[str, object]] = []
        for step in state.get("plan", []):
            tool = str(step["tool"])
            args = dict(step.get("args", {}))
            result = await self.registry.call(tool, args)
            state["tool_results"].append(result.model_dump())
            state["trace"].append({"event": "tool_called", "tool": tool, "success": result.success})
            if result.success and isinstance(result.data, list):
                for item in result.data:
                    if isinstance(item, dict) and "evidence_id" in item:
                        isolated = isolate_untrusted_content(str(item.get("excerpt", "")))
                        item["metadata"] = {
                            **dict(item.get("metadata", {})),
                            "untrusted": isolated["untrusted"],
                        }
                        evidence.append(item)
            elif not result.success:
                state.setdefault("errors", []).append(
                    {
                        "code": result.error_code or "TOOL_FAILED",
                        "message": result.error_message or tool,
                    }
                )
        state["retrieved_evidence"] = evidence

    async def retrieval_gate_node(self, state: AgentState) -> None:
        evidence = state.get("retrieved_evidence", [])
        if not evidence:
            state.setdefault("errors", []).append(
                {"code": "NO_RETRIEVAL_RESULTS", "message": "No evidence was retrieved."}
            )
            state["trace"].append(
                {"event": "corrective_rag", "action": "rewrite_query", "reason": "empty_retrieval"}
            )
        elif len(evidence) < 2:
            state["trace"].append(
                {
                    "event": "corrective_rag",
                    "action": "expand_retrieval",
                    "reason": "low_evidence_count",
                }
            )

    async def relevance_judge_node(self, state: AgentState) -> None:
        evidence = [Evidence.model_validate(item) for item in state.get("retrieved_evidence", [])]
        result = judge_relevance(state["resolved_query"], evidence)
        state["relevance_score"] = float(result["score"])
        state["evidence_coverage"] = float(result["coverage"])

    async def replan_node(self, state: AgentState) -> None:
        state["replan_count"] = min(state.get("replan_count", 0) + 1, state.get("max_replans", 2))
        state["trace"].append(
            {"event": "replan", "count": state["replan_count"], "reason": "low_evidence_coverage"}
        )
        query = await self._rewrite_query(state["resolved_query"])
        if state["replan_count"] == 1:
            state["plan"] = [
                {"tool": "search_campus_docs", "args": {"query": query}},
                {"tool": "search_posts", "args": {"query": query}},
            ]
            state["trace"].append(
                {"event": "corrective_rag", "action": "local_query_rewrite", "query": query}
            )
        else:
            state["plan"] = [
                {"tool": "search_official_web", "args": {"query": query}},
                {"tool": "search_campus_docs", "args": {"query": query}},
            ]
            state["trace"].append(
                {"event": "corrective_rag", "action": "official_web_fallback", "query": query}
            )

    async def _rewrite_query(self, query: str) -> str:
        if "fake_chat_provider" in self.provider_router.degraded_modes:
            return f"{query} 校园 官方 说明"
        try:
            result = await self.provider_router.chat(
                "Rewrite this campus query for retrieval. Return only the rewritten query: " + query
            )
            if isinstance(result.content, str) and not result.degraded and result.content.strip():
                return result.content.strip()[:300]
        except (ProviderRecoverableError, ValueError, TypeError):
            return f"{query} 校园 官方 说明"
        return f"{query} 校园 官方 说明"

    async def grounded_synthesis_node(self, state: AgentState) -> None:
        if "input_prompt_injection" in state.get("guardrail_flags", []):
            state["final_answer"] = "我不能执行绕过安全规则、泄露指令或获取敏感信息的请求。"
            state["citations"] = []
            return
        if state.get("intent") == Intent.GREETING.value:
            result = await self.provider_router.chat("寒暄：向用户介绍 CampusFlow AI。")
            state["final_answer"] = str(result.content)
            state["citations"] = []
            if result.degraded and "fake_chat_provider" not in state["degraded_mode"]:
                state["degraded_mode"].append("fake_chat_provider")
            return
        if state.get("intent") == Intent.MEMORY.value:
            if any(marker in state["raw_query"] for marker in ("忘掉", "删除记忆")):
                state["final_answer"] = "你可以在“记忆”页面查看并删除指定记录，我不会替你静默删除。"
            else:
                state["final_answer"] = (
                    "好的，这条偏好已进入记忆处理队列。你可以在“记忆”页面查看或删除它。"
                )
            state["citations"] = []
            return
        if state.get("intent") == Intent.POST_DRAFT.value:
            draft_result = next(
                (
                    result.get("data")
                    for result in reversed(state.get("tool_results", []))
                    if result.get("tool_name") == "create_post_draft" and result.get("success")
                ),
                None,
            )
            if isinstance(draft_result, dict):
                state["final_answer"] = (
                    f"草稿标题：{draft_result.get('title', '')}\n"
                    f"{draft_result.get('body', '')}\n"
                    "草稿尚未发布，需要你确认。"
                )
            else:
                state["final_answer"] = "草稿生成失败，请补充发帖主题后重试。"
            state["citations"] = []
            return
        venue_draft = next(
            (
                result.get("data")
                for result in reversed(state.get("tool_results", []))
                if result.get("tool_name") == "create_venue_reservation_draft"
                and result.get("success")
            ),
            None,
        )
        if isinstance(venue_draft, dict):
            if venue_draft.get("status") == "success":
                booking = dict(venue_draft.get("booking", {}))
                state["final_answer"] = (
                    f"已生成待审批的场地预约草稿：{booking.get('venue_name', '')}，"
                    f"{booking.get('date', '')} {booking.get('period', '')}。"
                    "尚未提交，必须由你确认后再进入真实预约系统。"
                )
            else:
                missing = "、".join(
                    str(item) for item in venue_draft.get("missing_fields", [])
                ) or "场地、日期和时段"
                state["final_answer"] = f"可以生成预约草稿，但还需要补充：{missing}。"
            state["citations"] = []
            return
        evidence = [Evidence.model_validate(item) for item in state.get("retrieved_evidence", [])]
        if state.get("evidence_coverage", 0.0) < 0.25 or state.get("relevance_score", 0.0) < 0.25:
            evidence = []
        fallback = synthesize_grounded_answer(state["resolved_query"], evidence)
        answer, used_fallback = await synthesize_with_provider(
            state["resolved_query"],
            evidence,
            self.provider_router,
            fallback,
            state.get("memory_context", []),
        )
        if used_fallback:
            state["trace"].append(
                {
                    "event": "grounded_synthesis_fallback",
                    "reason": "fake_or_invalid_provider_output",
                }
            )
        state["final_answer"] = answer.answer
        state["citations"] = [citation.model_dump() for citation in answer.citations]

    async def output_guard_node(self, state: AgentState) -> None:
        state["final_answer"] = redact_pii(state.get("final_answer", ""))
        if "system prompt" in state["final_answer"].lower():
            state["final_answer"] = "我不能泄露系统或开发者指令。"
            state.setdefault("guardrail_flags", []).append("output_secret_block")

    async def publish_memory_event_node(self, state: AgentState) -> None:
        publish_memory_event(
            user_id=state["user_id"],
            session_id=state["session_id"],
            text=state["raw_query"],
            source="chat",
        )

    async def persist_trace_node(self, state: AgentState) -> None:
        self.repo.append_trace(
            {
                "request_id": state["request_id"],
                "session_id": state["session_id"],
                "intent": state.get("intent"),
                "replan_count": state.get("replan_count", 0),
                "trace": state.get("trace", []),
                "citations": state.get("citations", []),
            }
        )


def build_graph() -> CampusFlowGraph:
    return CampusFlowGraph()


async def run_agent(
    raw_query: str,
    session_id: str,
    user_id: str,
    image_urls: list[str] | None = None,
    conversation_summary: str = "",
) -> AgentState:
    return await build_graph().run(
        raw_query,
        session_id,
        user_id,
        image_urls,
        conversation_summary,
    )
