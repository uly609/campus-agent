from __future__ import annotations

import base64
import json
from typing import Any

from app.agent.multi_agent.state import MultiAgentState
from app.llm.router import ProviderRouter
from app.multimodal.document_parser import parse_document_file
from app.retrieval.ingestion import build_corpus
from app.retrieval.service import RetrievalService
from app.services.repository import JsonRepository


class MultiAgentWorkers:
    def __init__(self, repo: JsonRepository | None = None, router: ProviderRouter | None = None) -> None:
        self.repo = repo or JsonRepository()
        self.router = router or ProviderRouter()
        self._retrieval: RetrievalService | None = None

    @staticmethod
    def _append(
        state: MultiAgentState,
        worker: str,
        content: str,
        artifact: dict[str, Any],
        *,
        degraded: bool = False,
        status: str = "completed",
    ) -> None:
        state["message_hub"].append({"agent": worker, "role": "worker", "content": content})
        state["artifacts"][worker] = artifact
        state["worker_results"].append(
            {
                "worker": worker,
                "status": status,
                "summary": content,
                "artifact_keys": sorted(artifact.keys()),
            }
        )
        state["trace"].append({"event": f"{worker}_completed", "worker": worker, "degraded": degraded})
        if degraded:
            state["degraded_mode"].append(f"{worker}:{artifact.get('mode', 'degraded')}")

    async def retrieval_worker(self, state: MultiAgentState) -> MultiAgentState:
        query = str(state.get("query", ""))
        documents = self.repo.load_documents()
        posts = self.repo.load_posts()
        if not documents and not posts:
            self._append(
                state,
                "retrieval_worker",
                "知识库为空，未执行检索。",
                {"kind": "retrieval", "evidence": [], "mode": "empty_corpus"},
            )
            return state
        try:
            if self._retrieval is None:
                self._retrieval = RetrievalService(build_corpus(posts, documents))
            evidence = await self._retrieval.search(query, top_k=5)
            payload = [
                {
                    "source_id": item.source_id,
                    "title": item.title,
                    "excerpt": item.excerpt,
                    "score": item.score,
                    "official": item.official,
                }
                for item in evidence
            ]
            self._append(
                state,
                "retrieval_worker",
                f"检索到 {len(payload)} 条校园知识结果。",
                {"kind": "retrieval", "evidence": payload, "mode": "hybrid_rag"},
            )
        except (OSError, RuntimeError, ValueError, KeyError) as exc:
            self._append(
                state,
                "retrieval_worker",
                f"检索失败：{type(exc).__name__}",
                {"kind": "retrieval", "evidence": [], "mode": "failed", "error": str(exc)[:200]},
                status="failed",
            )
        return state

    async def multimodal_worker(self, state: MultiAgentState) -> MultiAgentState:
        files = list(state.get("files", []))
        if not files:
            self._append(
                state,
                "multimodal_worker",
                "未提供文件附件；请先通过文件解析接口上传 Excel/PDF/图片。",
                {"kind": "multimodal", "chunks": [], "mode": "no_attachment"},
            )
            return state
        parsed_chunks: list[dict[str, Any]] = []
        degraded = False
        for item in files:
            name = str(item.get("name", "upload"))
            data_url = str(item.get("data_url", ""))
            try:
                raw = base64.b64decode(data_url.split(",", 1)[1])
                result = await parse_document_file(name, raw, self.router)
                for chunk in result.chunks:
                    parsed_chunks.append(
                        {
                            "chunk_id": chunk.chunk_id,
                            "kind": chunk.kind,
                            "title": chunk.title,
                            "text": chunk.text[:2000],
                            "metadata": chunk.metadata,
                        }
                    )
                degraded = degraded or any("演示" in warning or "离线" in warning for warning in result.warnings)
            except (ValueError, IndexError, UnicodeDecodeError) as exc:
                parsed_chunks.append({"chunk_id": name, "kind": "error", "title": name, "text": str(exc)[:200], "metadata": {}})
        self._append(
            state,
            "multimodal_worker",
            f"多模态解析完成，共 {len(parsed_chunks)} 个片段。",
            {"kind": "multimodal", "chunks": parsed_chunks, "mode": "document_parser"},
            degraded=degraded,
        )
        return state

    async def draft_worker(self, state: MultiAgentState) -> MultiAgentState:
        query = str(state.get("query", ""))
        result = await self.router.chat(
            f"请为浙江工商大学校园社区生成一段发帖草稿，主题为：{query}。"
            "要求：使用简体中文、语气自然、不编造具体人物联系方式。"
        )
        content = str(result.content)
        if result.degraded:
            content = f"【演示草稿】关于“{query}”的校园帖草稿。\n当前为离线演示模式，真实草稿需配置模型后生成。"
        self._append(
            state,
            "draft_worker",
            f"已生成发帖草稿（{len(content)} 字）。",
            {"kind": "draft", "draft": content, "mode": "degraded" if result.degraded else "llm"},
            degraded=result.degraded,
        )
        return state

    async def eval_worker(self, state: MultiAgentState) -> MultiAgentState:
        runs = self.repo.eval_runs()
        if not runs:
            summary = "暂无评测报告，请先调用 POST /api/v1/evals/run 生成评测。"
        else:
            latest = runs[-1]
            metrics = latest.get("metrics", {})
            summary = (
                f"最新评测 {latest.get('run_id', '')}："
                f"意图准确率 {metrics.get('intent_accuracy', 0):.2%}，"
                f"检索 MRR {metrics.get('retrieval_mrr_at_8', 0):.2f}，"
                f"引用忠实度 {metrics.get('qa_citation_faithfulness', 0):.2f}。"
            )
        self._append(
            state,
            "eval_worker",
            summary,
            {"kind": "eval", "summary": summary, "mode": "latest_report"},
        )
        return state

    async def general_worker(self, state: MultiAgentState) -> MultiAgentState:
        query = str(state.get("query", ""))
        result = await self.router.chat(
            f"请用简体中文回答以下校园通用问题，不要编造浙江工商大学的未公开信息：{query}"
        )
        content = str(result.content)
        if result.degraded:
            content = "当前是离线演示模式。通用问题请配置真实模型后获得更完整的回答；校园专属事实请使用 Agent 检索。"
        self._append(
            state,
            "general_worker",
            "已生成通用回答。",
            {"kind": "general", "answer": content, "mode": "degraded" if result.degraded else "llm"},
            degraded=result.degraded,
        )
        return state
