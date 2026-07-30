from __future__ import annotations

import logging
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import get_settings
from app.domain.schemas import Evidence

logger = logging.getLogger(__name__)


class _DrupalSearchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_results = False
        self.in_item = False
        self.item_depth = 0
        self.current_href = ""
        self.current_title = ""
        self.current_text: list[str] = []
        self.results: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = str(attributes.get("class") or "").split()
        if tag == "ol" and "search-results" in classes:
            self.in_results = True
            return
        if self.in_results and tag == "li" and not self.in_item:
            self.in_item = True
            self.item_depth = 1
            self.current_href = ""
            self.current_title = ""
            self.current_text = []
            return
        if self.in_item:
            if tag == "li":
                self.item_depth += 1
            if tag == "a" and not self.current_href:
                self.current_href = str(attributes.get("href") or "")

    def handle_endtag(self, tag: str) -> None:
        if self.in_item and tag == "li":
            self.item_depth -= 1
            if self.item_depth == 0:
                text = " ".join(" ".join(self.current_text).split())
                if self.current_href and text:
                    self.results.append(
                        {
                            "url": self.current_href,
                            "title": self.current_title or text[:80],
                            "content": text,
                        }
                    )
                self.in_item = False
        elif self.in_results and tag == "ol" and not self.in_item:
            self.in_results = False

    def handle_data(self, data: str) -> None:
        if not self.in_item:
            return
        normalized = " ".join(data.split())
        if not normalized:
            return
        if self.current_href and not self.current_title:
            self.current_title = normalized
        self.current_text.append(normalized)


class OfficialWebSearch:
    def __init__(self) -> None:
        settings = get_settings()
        self.endpoint = settings.official_web_search_url
        self.api_key = settings.official_web_search_api_key
        self.bailian_endpoint = settings.official_web_bailian_url
        self.bailian_api_key = settings.bailian_api_key
        self.bailian_model = settings.cloud_fallback_chat_model
        self.site_search_urls = tuple(
            item.strip()
            for item in settings.official_web_site_search_urls.split(",")
            if item.strip()
        )
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
        has_site_search = bool(self.site_search_urls)
        return bool(
            self.allowed_domains
            and (has_search_provider or has_bailian_search or has_site_search)
        )

    def _allowed(self, url: str) -> bool:
        host = (urlparse(url).hostname or "").lower()
        return any(host == domain or host.endswith(f".{domain}") for domain in self.allowed_domains)

    async def search(self, query: str, top_k: int = 5) -> list[Evidence]:
        if not self.configured:
            return []
        site_evidence = await self._search_site_indexes(query, top_k)
        if site_evidence:
            return site_evidence
        if self.endpoint and self.api_key:
            return await self._search_provider(query, top_k)
        if self.bailian_endpoint and self.bailian_api_key:
            return await self._search_bailian(query, top_k)
        return []

    @staticmethod
    def _site_search_term(query: str) -> str | None:
        if "辅导员" not in query or not any(
            marker in query for marker in ("计算机", "计科", "计算机科学与技术学院")
        ):
            return None
        year_match = re.search(r"20\d{2}级", query)
        return f"{year_match.group(0)}辅导员" if year_match else "辅导员"

    async def _search_site_indexes(self, query: str, top_k: int) -> list[Evidence]:
        term = self._site_search_term(query)
        if not term or not self.site_search_urls:
            return []
        evidence: list[Evidence] = []
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for search_url in self.site_search_urls:
                if not self._allowed(search_url):
                    continue
                try:
                    response = await client.get(search_url, params={"keys": term})
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    logger.warning(
                        "Official site search failed for %s: %s",
                        urlparse(search_url).hostname,
                        type(exc).__name__,
                    )
                    continue
                parser = _DrupalSearchParser()
                parser.feed(response.text)
                for item in parser.results:
                    url = urljoin(search_url, item["url"])
                    if not self._allowed(url):
                        continue
                    evidence.append(
                        Evidence(
                            evidence_id=f"site-search-{len(evidence) + 1}",
                            source_id=url,
                            source_type="official",
                            title=item["title"],
                            excerpt=item["content"][:500],
                            score=max(0.5, 1.0 - len(evidence) * 0.06),
                            official=True,
                            metadata={
                                "url": url,
                                "retrieval": "official-site-search",
                                "allowed_domain": "true",
                                "data_mode": "verified_official",
                                "excerpt_kind": "site_search_excerpt",
                                "search_term": term,
                            },
                        )
                    )
                    if len(evidence) >= top_k:
                        return evidence
        return evidence

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
