from __future__ import annotations

import re
from typing import Any

from app.agent.multi_agent.state import FINALIZE_NODE, WORKER_NAMES
from app.security.prompt_injection import detect_prompt_injection


class MultiAgentSupervisor:
    """Plan the minimum worker set once, then stop as soon as it is complete."""

    @staticmethod
    def required_workers(state: dict[str, Any]) -> list[str]:
        query = str(state.get("query", ""))
        selected: list[str] = []
        has_files = bool(state.get("files"))

        if has_files or re.search(r"Excel|PDF|文件|表格|拆分|扫描件", query, re.IGNORECASE):
            selected.append("multimodal_worker")
        if re.search(r"热门|推荐|点赞|举报|审核|治理|社区动态|帖子趋势", query):
            selected.append("community_worker")
        if re.search(r"评测|评估|指标|RAGAS|测试报告", query):
            selected.append("eval_worker")
        if re.search(r"发帖|草稿|发布", query):
            selected.append("draft_worker")
        campus_query = re.search(
            r"浙江工商大学|浙商大|学校|校园|课表|课程|场地|图书馆|食堂|辅导员|"
            r"校长|通知|教务|宿舍|校园卡|一卡通|奖学金|志愿|老师|教师|天气|下沙|教工路",
            query,
        )
        if campus_query and not ({"community_worker", "draft_worker"} & set(selected)):
            selected.append("campus_worker")
        elif campus_query and len(selected) > 0 and re.search(r"查询|查找|核实|规定|政策|场地|天气|通知", query):
            selected.append("campus_worker")

        if has_files and not ({"campus_worker", "draft_worker"} & set(selected)):
            selected.append("general_worker")

        if not selected:
            selected.append("general_worker")
        unique = set(selected)
        execution_order = (
            "multimodal_worker",
            "campus_worker",
            "retrieval_worker",
            "community_worker",
            "draft_worker",
            "eval_worker",
            "general_worker",
        )
        return [worker for worker in execution_order if worker in unique]

    async def route(self, state: dict[str, Any]) -> str:
        if state.get("guardrail_flags") or state.get("final_answer"):
            return FINALIZE_NODE
        executed = {str(item.get("worker")) for item in state.get("worker_results", [])}
        max_turns = int(state.get("max_turns", 4))
        required = list(state.get("required_workers", []))
        if required and all(worker in executed for worker in required):
            state["task_completed"] = True
            return FINALIZE_NODE
        if len(executed) >= max_turns:
            return FINALIZE_NODE
        for candidate in required:
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
            if not state.get("required_workers"):
                required = self.required_workers(state)[: int(state.get("max_turns", 4))]
                state["required_workers"] = required
                state["complexity"] = "single" if len(required) == 1 else "multi"
                state["message_hub"].append(
                    {
                        "agent": "supervisor",
                        "role": "plan",
                        "content": f"Selected workers: {', '.join(required)}.",
                        "required_workers": required,
                        "complexity": state["complexity"],
                    }
                )
            executed = {str(item.get("worker")) for item in state.get("worker_results", [])}
            required = list(state.get("required_workers", []))
            if required and all(worker in executed for worker in required):
                state["task_completed"] = True
                state["message_hub"].append(
                    {
                        "agent": "supervisor",
                        "role": "complete",
                        "content": "All required workers completed; finalize now.",
                    }
                )
                return state
            state["message_hub"].append(
                {
                    "agent": "supervisor",
                    "role": "dispatch",
                    "content": "Dispatch the next required worker.",
                }
            )
            state["turn_count"] = int(state.get("turn_count", 0)) + 1
        return state
