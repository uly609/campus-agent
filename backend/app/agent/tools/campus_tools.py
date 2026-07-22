from __future__ import annotations

import json
from pathlib import Path

from app.domain.enums import PostCategory
from app.domain.schemas import PostCreate, ToolResult
from app.multimodal.image_attributes import extract_image_attributes
from app.multimodal.ocr import verify_demo_student_card as verify_card
from app.retrieval.ingestion import build_corpus
from app.retrieval.service import RetrievalService
from app.services.repository import JsonRepository


class CampusTools:
    def __init__(self, repo: JsonRepository | None = None) -> None:
        self.repo = repo or JsonRepository()
        self._retrieval: RetrievalService | None = None

    async def retrieval(self) -> RetrievalService:
        if self._retrieval is None:
            self._retrieval = RetrievalService(build_corpus(self.repo.load_posts(), self.repo.load_documents()))
            await self._retrieval.rebuild()
        return self._retrieval

    async def search_campus_docs(self, payload: dict[str, object]) -> ToolResult:
        query = str(payload.get("query", ""))
        evidence = [item for item in await (await self.retrieval()).search(query) if item.official]
        return ToolResult(
            tool_name="search_campus_docs",
            success=True,
            data=[item.model_dump() for item in evidence],
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def search_posts(self, payload: dict[str, object]) -> ToolResult:
        query = str(payload.get("query", ""))
        evidence = [item for item in await (await self.retrieval()).search(query) if not item.official]
        return ToolResult(
            tool_name="search_posts",
            success=True,
            data=[item.model_dump() for item in evidence],
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def get_post_detail(self, payload: dict[str, object]) -> ToolResult:
        post = self.repo.find_post(str(payload.get("post_id", "")))
        if not post:
            return ToolResult(
                tool_name="get_post_detail",
                success=False,
                data=None,
                error_code="POST_NOT_FOUND",
                error_message="Post was not found.",
                latency_ms=0,
                provenance=[],
            )
        return ToolResult(
            tool_name="get_post_detail",
            success=True,
            data=post.model_dump(),
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def search_lost_and_found(self, payload: dict[str, object]) -> ToolResult:
        query = str(payload.get("query", ""))
        posts = [
            post.model_dump()
            for post in self.repo.load_posts()
            if post.category == PostCategory.LOST_FOUND and (query in post.title or query in post.body or not query)
        ][:12]
        return ToolResult(
            tool_name="search_lost_and_found",
            success=True,
            data=posts,
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def get_campus_events(self, payload: dict[str, object]) -> ToolResult:
        events = [
            {"event_id": "event-library-talk", "title": "图书馆信息素养讲座", "location": "图书馆", "time": "周三 19:00"},
            {"event_id": "event-sports-night", "title": "体育馆夜跑活动", "location": "体育馆", "time": "周五 20:00"},
        ]
        return ToolResult(
            tool_name="get_campus_events",
            success=True,
            data=events,
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def get_campus_service_info(self, payload: dict[str, object]) -> ToolResult:
        query = str(payload.get("query", "服务"))
        docs = [doc for doc in self.repo.load_documents() if query[:2] in doc["body"] or query[:2] in doc["title"]]
        return ToolResult(
            tool_name="get_campus_service_info",
            success=True,
            data=docs[:8],
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def analyze_post_image(self, payload: dict[str, object]) -> ToolResult:
        image_url = str(payload.get("image_url", ""))
        attrs = await extract_image_attributes(image_url)
        return ToolResult(
            tool_name="analyze_post_image",
            success=True,
            data=attrs,
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def verify_demo_student_card(self, payload: dict[str, object]) -> ToolResult:
        result = verify_card(str(payload.get("image_url", "")), str(payload.get("visible_text", "")))
        return ToolResult(
            tool_name="verify_demo_student_card",
            success=bool(result["verified"]),
            data=result,
            error_code=str(result["error_code"]) if result.get("error_code") else None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def create_post_draft(self, payload: dict[str, object]) -> ToolResult:
        intent = str(payload.get("intent", ""))
        attrs = payload.get("image_attributes", {})
        if not isinstance(attrs, dict):
            attrs = {}
        title = str(payload.get("title") or f"{attrs.get('location_hints', ['校园'])[0]}失物招领")
        body = str(payload.get("body") or f"根据图片线索，物品可能是{attrs.get('color', '')}{attrs.get('category', '物品')}。请同学核对后再发布。")
        draft = {
            "draft_id": "draft-demo",
            "title": title,
            "body": body,
            "category": PostCategory.LOST_FOUND.value if "失物" in title or intent else PostCategory.LIFE.value,
            "tags": ["AI草稿", str(attrs.get("category", "校园"))],
            "edit_round": int(str(payload.get("edit_round", 0))),
            "requires_confirmation": True,
        }
        return ToolResult(
            tool_name="create_post_draft",
            success=True,
            data=draft,
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def load_user_memories(self, payload: dict[str, object]) -> ToolResult:
        memories = self.repo.load_memories(str(payload.get("user_id", "demo-user")))
        return ToolResult(
            tool_name="load_user_memories",
            success=True,
            data=[memory.model_dump() for memory in memories],
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def save_memory_feedback(self, payload: dict[str, object]) -> ToolResult:
        return ToolResult(
            tool_name="save_memory_feedback",
            success=True,
            data={"accepted": True},
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def get_eval_report(self, payload: dict[str, object]) -> ToolResult:
        report_path = Path("evals/reports/latest.json")
        if not report_path.exists():
            return ToolResult(
                tool_name="get_eval_report",
                success=False,
                data=None,
                error_code="EVAL_REPORT_NOT_FOUND",
                error_message="Run the evaluation suite before requesting its report.",
                latency_ms=0,
                provenance=[],
            )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        summary = json.dumps(report.get("metrics", {}), ensure_ascii=False, sort_keys=True)
        return ToolResult(
            tool_name="get_eval_report",
            success=True,
            data=[
                {
                    "evidence_id": f"eval-{report.get('run_id', 'latest')}",
                    "source_id": str(report.get("run_id", "latest")),
                    "source_type": "official",
                    "title": "CampusFlow evaluation report",
                    "excerpt": summary,
                    "score": 1.0,
                    "official": True,
                    "metadata": {"report_path": str(report_path)},
                }
            ],
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[{"path": str(report_path), "kind": "evaluation_report"}],
        )


def build_registry(tools: CampusTools | None = None):
    from app.agent.tools.registry import ToolRegistry

    active = tools or CampusTools()
    registry = ToolRegistry()
    registry.register("search_campus_docs", active.search_campus_docs)
    registry.register("search_posts", active.search_posts)
    registry.register("get_post_detail", active.get_post_detail)
    registry.register("search_lost_and_found", active.search_lost_and_found)
    registry.register("get_campus_events", active.get_campus_events)
    registry.register("get_campus_service_info", active.get_campus_service_info)
    registry.register("analyze_post_image", active.analyze_post_image)
    registry.register("verify_demo_student_card", active.verify_demo_student_card)
    registry.register("create_post_draft", active.create_post_draft)
    registry.register("load_user_memories", active.load_user_memories)
    registry.register("save_memory_feedback", active.save_memory_feedback)
    registry.register("get_eval_report", active.get_eval_report)
    return registry
