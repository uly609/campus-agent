from __future__ import annotations

import time
import uuid
from typing import Any, Awaitable, Callable, Literal

from langgraph.graph import END, START, StateGraph

from app.agent.policies import judge_relevance, synthesize_grounded_answer
from app.agent.planning import plan_intent
from app.agent.grounded_llm import synthesize_with_provider
from app.agent.state import AgentState, REQUIRED_NODES, SIX_STAGES
from app.agent.tools.campus_tools import build_registry
from app.domain.enums import Intent
from app.domain.schemas import Citation, Evidence
from app.memory.producer import publish_memory_event
from app.llm.router import ProviderRouter
from app.multimodal.image_attributes import enhance_query_with_image
from app.security.pii import redact_pii
from app.security.prompt_injection import detect_prompt_injection, isolate_untrusted_content
from app.services.repository import JsonRepository


NodeCallable = Callable[[AgentState], Any]
GraphRoute = Literal["visual_understanding_node", "intent_planner_node", "tool_executor_node", "grounded_synthesis_node", "replan_node"]


class CampusFlowGraph:
    def __init__(self, repo: JsonRepository | None = None) -> None:
        self.repo = repo or JsonRepository()
        self.provider_router = ProviderRouter()
        self.registry = build_registry()
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
        return "grounded_synthesis_node" if state.get("intent") == Intent.GREETING.value else "tool_executor_node"

    @staticmethod
    def _route_relevance(state: AgentState) -> GraphRoute:
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

    async def run(self, raw_query: str, session_id: str, user_id: str, image_urls: list[str] | None = None) -> AgentState:
        state: AgentState = {
            "request_id": f"req-{uuid.uuid4().hex[:12]}",
            "session_id": session_id,
            "user_id": user_id,
            "raw_query": raw_query,
            "image_urls": image_urls or [],
            "image_context": [],
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
        state["memory_context"] = list(result.data or [])
        state["tool_results"].append(result.model_dump())

    async def coreference_resolver_node(self, state: AgentState) -> None:
        query = state["raw_query"]
        summary = state.get("conversation_summary", "")
        if "它" in query and summary:
            query = query.replace("它", summary[:40])
        state["resolved_query"] = query

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
        intent, plan, confidence = plan_intent(query, state["user_id"])
        state["intent"] = intent.value
        state["intent_confidence"] = confidence
        state["plan"] = plan
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
                        item["metadata"] = {**dict(item.get("metadata", {})), "untrusted": isolated["untrusted"]}
                        evidence.append(item)
            elif not result.success:
                state.setdefault("errors", []).append({"code": result.error_code or "TOOL_FAILED", "message": result.error_message or tool})
        state["retrieved_evidence"] = evidence

    async def retrieval_gate_node(self, state: AgentState) -> None:
        if not state.get("retrieved_evidence"):
            state.setdefault("errors", []).append({"code": "NO_RETRIEVAL_RESULTS", "message": "No evidence was retrieved."})

    async def relevance_judge_node(self, state: AgentState) -> None:
        evidence = [Evidence.model_validate(item) for item in state.get("retrieved_evidence", [])]
        result = judge_relevance(state["resolved_query"], evidence)
        state["relevance_score"] = float(result["score"])
        state["evidence_coverage"] = float(result["coverage"])

    async def replan_node(self, state: AgentState) -> None:
        state["replan_count"] = min(state.get("replan_count", 0) + 1, state.get("max_replans", 2))
        state["trace"].append({"event": "replan", "count": state["replan_count"], "reason": "low_evidence_coverage"})
        if state["replan_count"] >= state.get("max_replans", 2):
            return
        query = state["resolved_query"] + " 校园 官方 说明"
        state["plan"] = [{"tool": "search_campus_docs", "args": {"query": query}}, {"tool": "search_posts", "args": {"query": query}}]

    async def grounded_synthesis_node(self, state: AgentState) -> None:
        if state.get("intent") == Intent.GREETING.value:
            result = await self.provider_router.chat("寒暄：向用户介绍 CampusFlow AI。")
            state["final_answer"] = str(result.content)
            state["citations"] = []
            if result.degraded and "fake_chat_provider" not in state["degraded_mode"]:
                state["degraded_mode"].append("fake_chat_provider")
            return
        evidence = [Evidence.model_validate(item) for item in state.get("retrieved_evidence", [])]
        if state.get("evidence_coverage", 0.0) < 0.25 or state.get("relevance_score", 0.0) < 0.25:
            evidence = []
        fallback = synthesize_grounded_answer(state["resolved_query"], evidence)
        answer, used_fallback = await synthesize_with_provider(
            state["resolved_query"], evidence, self.provider_router, fallback
        )
        if used_fallback:
            state["trace"].append({"event": "grounded_synthesis_fallback", "reason": "fake_or_invalid_provider_output"})
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


async def run_agent(raw_query: str, session_id: str, user_id: str, image_urls: list[str] | None = None) -> AgentState:
    return await build_graph().run(raw_query, session_id, user_id, image_urls)
