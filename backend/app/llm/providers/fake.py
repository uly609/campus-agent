from __future__ import annotations

from app.llm.base import ProviderRecoverableError
from app.retrieval.embeddings import embed_text


class FakeChatProvider:
    def __init__(self, name: str = "local_primary", should_fail: bool = False) -> None:
        self.name = name
        self.model = "fake-campus-chat"
        self.should_fail = should_fail

    async def complete(self, prompt: str) -> str:
        if self.should_fail:
            raise ProviderRecoverableError("simulated connection failure")
        if "寒暄" in prompt or "你好" in prompt:
            return "你好，我是 CampusFlow AI，可以帮你查校园信息、找帖子或起草匿名帖。"
        return "根据已检索证据，我将给出带引用的校园回答。"


class FakeEmbeddingProvider:
    def __init__(self, name: str = "local_primary", should_fail: bool = False) -> None:
        self.name = name
        self.model = "fake-bge-m3-compatible"
        self.should_fail = should_fail

    async def embed(self, text: str) -> list[float]:
        if self.should_fail:
            raise ProviderRecoverableError("simulated embedding outage")
        return embed_text(text)


class FakeVLMProvider:
    def __init__(self, name: str = "local_primary", should_fail: bool = False) -> None:
        self.name = name
        self.model = "fake-qwen2.5-vl"
        self.should_fail = should_fail

    async def analyze(self, image_url: str, prompt: str) -> dict[str, object]:
        if self.should_fail:
            raise ProviderRecoverableError("simulated vlm outage")
        lowered = image_url.lower()
        category = "校园卡" if "card" in lowered else "失物"
        color = "蓝色" if "blue" in lowered or "card" in lowered else "黑色"
        return {
            "category": category,
            "color": color,
            "brand": "",
            "material": "塑料" if category == "校园卡" else "未知",
            "visible_text": "SYNTHETIC DEMO" if category == "校园卡" else "",
            "location_hints": ["图书馆"] if "library" in lowered else ["学生服务中心"],
            "confidence": 0.82,
            "safety_flags": [],
            "degraded_mode": True,
        }

