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
        self.allowed_domains = tuple(
            item.strip().lower()
            for item in settings.official_web_allowed_domains.split(",")
            if item.strip()
        )
        self.timeout = settings.provider_timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.api_key and self.allowed_domains)

    def _allowed(self, url: str) -> bool:
        host = (urlparse(url).hostname or "").lower()
        return any(host == domain or host.endswith(f".{domain}") for domain in self.allowed_domains)

    async def search(self, query: str, top_k: int = 5) -> list[Evidence]:
        if not self.configured:
            return []
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
                    },
                )
            )
        return evidence
