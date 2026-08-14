from __future__ import annotations

import httpx
import pytest

from app.agent.tools.knowledge_tools import KnowledgeCommunityTools
from app.domain.schemas import Evidence
from app.retrieval.official_web import OfficialWebSearch


@pytest.mark.asyncio
async def test_official_web_returns_explicit_degraded_result_without_credentials() -> None:
    search = OfficialWebSearch()
    search.endpoint = ""
    search.api_key = ""
    search.bailian_api_key = ""
    search.allowed_domains = ()
    tools = KnowledgeCommunityTools()
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

    tools = KnowledgeCommunityTools()
    tools._retrieval = FakeRetrieval()  # type: ignore[assignment]
    tools._official_web = FakeOfficialWeb()  # type: ignore[assignment]

    result = await tools.search_knowledge_base({"query": "企业现任负责人信息"})

    assert result.success is True
    assert result.provenance[0]["kind"] == "official_web_fallback"
    assert result.data and result.data[0]["title"] == "学校领导"


@pytest.mark.asyncio
async def test_computer_college_advisor_query_uses_official_site_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    html = """
    <ol class="search-results node_search-results">
      <li>
        <h3><a href="/zh-hans/node/2660">计算机学院转专业学生交流座谈会</a></h3>
        <p>学院党委书记等领导、2024级辅导员沈一品及2024级班主任出席会议。</p>
      </li>
    </ol>
    """

    class FakeClient:
        def __init__(self, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def get(self, url, **kwargs):
            request = httpx.Request("GET", str(url))
            return httpx.Response(200, request=request, text=html)

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    search = OfficialWebSearch()
    search.endpoint = ""
    search.api_key = ""
    search.bailian_api_key = ""
    search.allowed_domains = ("zjgsu.edu.cn",)
    search.site_search_urls = (
        "https://scie.zjgsu.edu.cn/zh-hans/search/node",
    )

    evidence = await search.search("计算机科学与技术学院2024级本科生辅导员信息")

    assert evidence[0].source_id == "https://scie.zjgsu.edu.cn/zh-hans/node/2660"
    assert "2024级辅导员沈一品" in evidence[0].excerpt
    assert evidence[0].metadata["retrieval"] == "official-site-search"
    assert evidence[0].metadata["search_term"] == "2024级辅导员"


@pytest.mark.asyncio
async def test_site_search_failure_falls_back_to_bailian(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    search = OfficialWebSearch()
    search.endpoint = ""
    search.api_key = ""
    search.bailian_api_key = "configured"
    search.allowed_domains = ("zjgsu.edu.cn",)
    search.site_search_urls = (
        "https://scie.zjgsu.edu.cn/zh-hans/search/node",
    )

    async def failed_site_search(query: str, top_k: int):
        return []

    expected = [
        Evidence(
            evidence_id="web-1",
            source_id="https://www.zjgsu.edu.cn/example",
            source_type="official",
            title="官网结果",
            excerpt="官网内容",
            score=1.0,
            official=True,
        )
    ]

    async def bailian_search(query: str, top_k: int):
        return expected

    monkeypatch.setattr(search, "_search_site_indexes", failed_site_search)
    monkeypatch.setattr(search, "_search_bailian", bailian_search)

    evidence = await search.search("计算机专业2024级辅导员是谁")

    assert evidence == expected
