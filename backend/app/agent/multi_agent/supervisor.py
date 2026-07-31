from __future__ import annotations

import re
from typing import Any

from app.agent.multi_agent.state import FINALIZE_NODE, WORKER_NAMES
from app.security.prompt_injection import detect_prompt_injection


class MultiAgentSupervisor:
    """Deterministic supervisor that routes one new worker per turn."""

    @staticmethod
    def _candidates(state: dict[str, Any]) -> list[str]:
        query = str(state.get("query", ""))
        if re.search(r"图片|Excel|PDF|文件|上传|识别|拆分|扫描", query):
            return ["multimodal_worker", *[name for name in WORKER_NAMES if name != "multimodal_worker"]]
        if re.search(r"评测|评估|指标|RAGAS|测试报告", query):
            return ["eval_worker", *[name for name in WORKER_NAMES if name != "eval_worker"]]
        if re.search(r"发帖|帖子|草稿|社区|发布", query):
            return ["draft_worker", *[name for name in WORKER_NAMES if name != "draft_worker"]]
        if re.search(r"知识|课表|场地|图书馆|食堂|辅导员|校长|通知|搜索|找|服务|政策", query):
            return ["retrieval_worker", *[name for name in WORKER_NAMES if name != "retrieval_worker"]]
        return list(WORKER_NAMES)

    async def route(self, state: dict[str, Any]) -> str:
        if state.get("guardrail_flags") or state.get("final_answer"):
            return FINALIZE_NODE
        executed = {str(item.get("worker")) for item in state.get("worker_results", [])}
        max_turns = int(state.get("max_turns", 4))
        if len(executed) >= max_turns or int(state.get("turn_count", 0)) > max_turns * 2:
            return FINALIZE_NODE
        for candidate in self._candidates(state):
            if candidate not in executed:
                return candidate
        return FINALIZE_NODE

    async def supervise(self, state: dict[str, Any]) -> dict[str, Any]:
        query = str(state.get("query", ""))
        flags = detect_prompt_injection(query)
        if flags:
            state["guardrail_flags"] = flags
            state["final_answer"] = "检测到可疑指令注入，已停止多 Agent 协作。请用正常校园问题重试。"
            state["message_hub"].append(
                {
                    "agent": "supervisor",
                    "role": "guardrail",
                    "content": "Prompt injection flags detected; routing to finalize.",
                    "flags": flags,
                }
            )
        else:
            state["turn_count"] = int(state.get("turn_count", 0)) + 1
            state["message_hub"].append(
                {
                    "agent": "supervisor",
                    "role": "plan",
                    "content": f"Turn {state['turn_count']}: plan and dispatch next worker.",
                }
            )
        return state
