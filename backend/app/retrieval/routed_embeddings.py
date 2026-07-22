from __future__ import annotations

from app.llm.router import ProviderRouter


class RoutedEmbeddingProvider:
    provider_name = "routed-embedding"

    def __init__(self, router: ProviderRouter | None = None) -> None:
        self.router = router or ProviderRouter()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in texts:
            result = await self.router.embed(text)
            if not isinstance(result.content, list):
                raise ValueError("embedding provider returned a non-vector result")
            embeddings.append([float(value) for value in result.content])
        return embeddings
