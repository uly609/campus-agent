from __future__ import annotations

import pytest

from app.agent.tools.campus_tools import CampusTools
from app.retrieval.official_web import OfficialWebSearch


@pytest.mark.asyncio
async def test_official_web_returns_explicit_degraded_result_without_credentials() -> None:
    search = OfficialWebSearch()
    search.endpoint = ""
    search.api_key = ""
    search.allowed_domains = ()
    tools = CampusTools()
    tools._official_web = search

    result = await tools.search_official_web({"query": "最新校历"})

    assert result.success is False
    assert result.error_code == "OFFICIAL_WEB_SEARCH_NOT_CONFIGURED"
    assert result.data is None
