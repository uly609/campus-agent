from __future__ import annotations

import httpx
import pytest

from app.agent.tools.campus_tools import CampusTools
from app.domain.schemas import Evidence
from app.retrieval.official_web import OfficialWebSearch


@pytest.mark.asyncio
async def test_official_web_returns_explicit_degraded_result_without_credentials() -> None:
    search = OfficialWebSearch()
    search.endpoint = ""
    search.api_key = ""
    search.bailian_api_key = ""
    search.allowed_domains = ()
    tools = CampusTools()
    tools._official_web = search

    result = await tools.search_official_web({"query": "最新校历"})

    assert result.success is False
    assert result.error_code == "OFFICIAL_WEB_SEARCH_NOT_CONFIGURED"
    assert result.data is None


@pytest.mark.asyncio
async def test_bailian_web_search_keeps_only_allowlisted_official_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        def __init__(self, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def post(self, url, **kwargs):
            request = httpx.Request("POST", str(url))
            return httpx.Response(
                200,
                request=request,
                json={
                    "output": {
                        "choices": [
                            {"message": {"content": "浙江工商大学官网搜索摘要"}}
                        ],
                        "search_info": {
                            "search_results": [
                                {
                                    "title": "学校领导",
                                    "url": "https://www.zjgsu.edu.cn/leader",
                                },
                                {
                                    "title": "非学校来源",
                                    "url": "https://example.com/leader",
                                },
                            ]
                        },
                    }
                },
            )

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    search = OfficialWebSearch()
    search.endpoint = ""
    search.api_key = ""
    search.bailian_api_key = "configured-for-test"
    search.allowed_domains = ("zjgsu.edu.cn",)

    evidence = await search.search("校长是谁")

    assert len(evidence) == 1
    assert evidence[0].title == "学校领导"
    assert evidence[0].metadata["data_mode"] == "verified_official"
    assert evidence[0].metadata["excerpt_kind"] == "search_summary"


@pytest.mark.asyncio
async def test_campus_docs_falls_back_to_official_web_when_local_rag_misses() -> None:
    unrelated = Evidence(
        evidence_id="local-1",
        source_id="library",
        source_type="official",
        title="图书馆借阅规则",
        excerpt="校园卡可以用于借阅图书。",
        score=0.8,
        official=True,
        metadata={"data_mode": "verified_official"},
    )
    official = Evidence(
        evidence_id="web-1",
        source_id="https://www.zjgsu.edu.cn/leader",
        source_type="official",
        title="学校领导",
        excerpt="浙江工商大学官网搜索摘要",
        score=0.9,
        official=True,
        metadata={"data_mode": "verified_official", "url": "https://www.zjgsu.edu.cn/leader"},
    )

    class FakeRetrieval:
        async def search(self, query, source_type=None):
            return [unrelated]

    class FakeOfficialWeb:
        configured = True

        async def search(self, query):
            return [official]

    tools = CampusTools()
    tools._retrieval = FakeRetrieval()  # type: ignore[assignment]
    tools._official_web = FakeOfficialWeb()  # type: ignore[assignment]

    result = await tools.search_campus_docs({"query": "浙江工商大学现任校长信息"})

    assert result.success is True
    assert result.provenance[0]["kind"] == "official_web_fallback"
    assert result.data and result.data[0]["title"] == "学校领导"
