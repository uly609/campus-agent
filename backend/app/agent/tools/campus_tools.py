from __future__ import annotations

import json

import httpx
from pathlib import Path

from app.domain.enums import PostCategory
from app.campus_skills.adapters import (
    course_evidence,
    notice_evidence,
    profile_evidence,
    reservation_draft,
    venue_evidence,
    weather_evidence,
)
from app.domain.schemas import Evidence, PostCreate, ToolResult
from app.multimodal.image_attributes import extract_image_attributes
from app.multimodal.ocr import verify_demo_student_card as verify_card
from app.retrieval.ingestion import build_corpus
from app.retrieval.official_web import OfficialWebSearch
from app.retrieval.service import RetrievalService
from app.services.post_service import create_draft, draft_to_dict
from app.services.repository import JsonRepository


_shared_retrieval: RetrievalService | None = None


class CampusTools:
    def __init__(self, repo: JsonRepository | None = None) -> None:
        self.repo = repo or JsonRepository()
        self._retrieval: RetrievalService | None = None
        self._official_web = OfficialWebSearch()

    async def retrieval(self) -> RetrievalService:
        global _shared_retrieval
        if self._retrieval is None:
            if _shared_retrieval is None:
                _shared_retrieval = RetrievalService(
                    build_corpus(self.repo.load_posts(), self.repo.load_documents())
                )
                await _shared_retrieval.rebuild()
            self._retrieval = _shared_retrieval
        return self._retrieval

    async def search_campus_docs(self, payload: dict[str, object]) -> ToolResult:
        query = str(payload.get("query", ""))
        evidence = [item for item in await (await self.retrieval()).search(query, source_type="official") if item.official]
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
        evidence = [
            item for item in await (await self.retrieval()).search(query, source_type="post") if not item.official
        ]
        return ToolResult(
            tool_name="search_posts",
            success=True,
            data=[item.model_dump() for item in evidence],
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[],
        )

    async def search_official_web(self, payload: dict[str, object]) -> ToolResult:
        query = str(payload.get("query", ""))
        if not self._official_web.configured:
            return ToolResult(
                tool_name="search_official_web",
                success=False,
                data=None,
                error_code="OFFICIAL_WEB_SEARCH_NOT_CONFIGURED",
                error_message="Official web search is unavailable; local retrieval remains active.",
                latency_ms=0,
                provenance=[],
            )
        try:
            evidence = await self._official_web.search(query)
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            return ToolResult(
                tool_name="search_official_web",
                success=False,
                data=None,
                error_code="OFFICIAL_WEB_SEARCH_FAILED",
                error_message=exc.__class__.__name__,
                latency_ms=0,
                provenance=[],
            )
        return ToolResult(
            tool_name="search_official_web",
            success=True,
            data=[item.model_dump() for item in evidence],
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[{"kind": "official_web", "allowlisted": True}],
        )

    async def query_course_schedule(self, payload: dict[str, object]) -> ToolResult:
        evidence = course_evidence(payload)
        return self._evidence_result("query_course_schedule", evidence)

    async def query_campus_notices(self, payload: dict[str, object]) -> ToolResult:
        evidence = notice_evidence(payload)
        return self._evidence_result("query_campus_notices", evidence)

    async def query_campus_venues(self, payload: dict[str, object]) -> ToolResult:
        evidence = venue_evidence(payload)
        return self._evidence_result("query_campus_venues", evidence)

    async def query_campus_weather(self, payload: dict[str, object]) -> ToolResult:
        evidence, error = await weather_evidence(payload)
        if error:
            return ToolResult(tool_name="query_campus_weather", success=False, data=None, error_code="WEATHER_SERVICE_UNAVAILABLE", error_message=error, latency_ms=0, provenance=[])
        return self._evidence_result("query_campus_weather", evidence)

    async def get_student_profile(self, payload: dict[str, object]) -> ToolResult:
        return self._evidence_result("get_student_profile", profile_evidence())

    async def create_venue_reservation_draft(self, payload: dict[str, object]) -> ToolResult:
        draft = reservation_draft(payload)
        success = draft.get("status") != "error"
        return ToolResult(tool_name="create_venue_reservation_draft", success=success, data=draft, error_code=None if success else "VENUE_DRAFT_INVALID", error_message=None if success else str(draft.get("message")), latency_ms=0, provenance=[{"kind": "xiaolin_authorized_adaptation", "synthetic_demo": True}])

    @staticmethod
    def _evidence_result(tool_name: str, evidence: list[Evidence]) -> ToolResult:
        return ToolResult(
            tool_name=tool_name,
            success=True,
            data=[item.model_dump() for item in evidence],
            error_code=None,
            error_message=None,
            latency_ms=0,
            provenance=[{"kind": "xiaolin_authorized_adaptation", "synthetic_demo": True}],
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
            if post.category == PostCategory.LOST_FOUND
            and (query in post.title or query in post.body or not query)
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
            {
                "event_id": "event-library-talk",
                "title": "图书馆信息素养讲座",
                "location": "图书馆",
                "time": "周三 19:00",
            },
            {
                "event_id": "event-sports-night",
                "title": "体育馆夜跑活动",
                "location": "体育馆",
                "time": "周五 20:00",
            },
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
        docs = [
            doc
            for doc in self.repo.load_documents()
            if query[:2] in doc["body"] or query[:2] in doc["title"]
        ]
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
        result = verify_card(
            str(payload.get("image_url", "")), str(payload.get("visible_text", ""))
        )
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
        requested = payload.get("category")
        category = PostCategory(str(requested)) if requested else None
        draft = draft_to_dict(create_draft(intent, attrs, category))
        draft["requires_confirmation"] = True
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
    registry.register("search_official_web", active.search_official_web)
    registry.register("query_course_schedule", active.query_course_schedule)
    registry.register("query_campus_notices", active.query_campus_notices)
    registry.register("query_campus_venues", active.query_campus_venues)
    registry.register("query_campus_weather", active.query_campus_weather)
    registry.register("get_student_profile", active.get_student_profile)
    registry.register("create_venue_reservation_draft", active.create_venue_reservation_draft)
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
