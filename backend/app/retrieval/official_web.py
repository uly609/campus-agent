from __future__ import annotations

from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.domain.schemas import Evidence


class OfficialWebSearch:
    def __init__(self) -> None:
        settings = get_settings()
        self.endpoint = settings.official_web_search_url
        self.api_key = settings.official_web_search_api_key
        self.bailian_endpoint = settings.official_web_bailian_url
        self.bailian_api_key = settings.bailian_api_key
        self.bailian_model = settings.cloud_fallback_chat_model
        self.allowed_domains = tuple(
            item.strip().lower()
            for item in settings.official_web_allowed_domains.split(",")
            if item.strip()
        )
        self.timeout = settings.provider_timeout_seconds

    @property
    def configured(self) -> bool:
        has_search_provider = bool(self.endpoint and self.api_key)
        has_bailian_search = bool(self.bailian_endpoint and self.bailian_api_key)
        return bool(self.allowed_domains and (has_search_provider or has_bailian_search))

    def _allowed(self, url: str) -> bool:
        host = (urlparse(url).hostname or "").lower()
        return any(host == domain or host.endswith(f".{domain}") for domain in self.allowed_domains)

    async def search(self, query: str, top_k: int = 5) -> list[Evidence]:
        if not self.configured:
            return []
        if self.endpoint and self.api_key:
            return await self._search_provider(query, top_k)
        return await self._search_bailian(query, top_k)

    async def _search_provider(self, query: str, top_k: int) -> list[Evidence]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                str(self.endpoint),
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": top_k,
                    "include_domains": list(self.allowed_domains),
                },
            )
            response.raise_for_status()
        payload = response.json()
        results = payload.get("results", []) if isinstance(payload, dict) else []
        evidence: list[Evidence] = []
        for index, item in enumerate(results[:top_k], start=1):
            if not isinstance(item, dict) or not self._allowed(str(item.get("url", ""))):
                continue
            url = str(item["url"])
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            evidence.append(
                Evidence(
                    evidence_id=f"web-{index}",
                    source_id=url,
                    source_type="official",
                    title=str(item.get("title", url)),
                    excerpt=content[:500],
                    score=float(item.get("score", 0.5)),
                    official=True,
                    metadata={
                        "url": url,
                        "retrieval": "official-web-search",
                        "allowed_domain": "true",
                        "data_mode": "verified_official",
                    },
                )
            )
        return evidence

    async def _search_bailian(self, query: str, top_k: int) -> list[Evidence]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.bailian_endpoint,
                headers={
                    "Authorization": f"Bearer {self.bailian_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.bailian_model,
                    "input": {
                        "messages": [
                            {
                                "role": "user",
                                "content": (
                                    f"请查询并回答以下问题，只使用浙江工商大学官网信息：{query}"
                                ),
                            }
                        ]
                    },
                    "parameters": {
                        "enable_search": True,
                        "search_options": {
                            "forced_search": True,
                            "enable_source": True,
                            "search_strategy": "turbo",
                            "assigned_site_list": list(self.allowed_domains),
                        },
                        "result_format": "message",
                    },
                },
            )
            response.raise_for_status()

        payload = response.json()
        output = payload.get("output", {}) if isinstance(payload, dict) else {}
        choices = output.get("choices", []) if isinstance(output, dict) else []
        message = choices[0].get("message", {}) if choices and isinstance(choices[0], dict) else {}
        summary = str(message.get("content", "")).strip()
        search_info = output.get("search_info", {}) if isinstance(output, dict) else {}
        results = search_info.get("search_results", []) if isinstance(search_info, dict) else []

        evidence: list[Evidence] = []
        for index, item in enumerate(results[:top_k], start=1):
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", ""))
            if not self._allowed(url):
                continue
            title = str(item.get("title", "")).strip() or url
            content = str(item.get("snippet") or item.get("content") or summary).strip()
            if not content:
                content = f"百炼官网搜索找到相关页面：{title}"
            evidence.append(
                Evidence(
                    evidence_id=f"bailian-web-{index}",
                    source_id=url,
                    source_type="official",
                    title=title,
                    excerpt=content[:500],
                    score=max(0.5, 1.0 - (index - 1) * 0.08),
                    official=True,
                    metadata={
                        "url": url,
                        "retrieval": "bailian-official-web-search",
                        "allowed_domain": "true",
                        "data_mode": "verified_official",
                        "excerpt_kind": "search_summary",
                    },
                )
            )
        return evidence
