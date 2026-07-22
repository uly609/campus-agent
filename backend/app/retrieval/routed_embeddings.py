from __future__ import annotations

from app.llm.router import ProviderRouter


class RoutedEmbeddingProvider:
    provider_name = "routed-embedding"
    batch_size = 10

    def __init__(self, router: ProviderRouter | None = None) -> None:
        self.router = router or ProviderRouter()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            result = await self.router.embed_many(batch)
            if not isinstance(result.content, list) or len(result.content) != len(batch):
                raise ValueError("embedding provider returned an invalid batch")
            for vector in result.content:
                if not isinstance(vector, list):
                    raise ValueError("embedding provider returned a non-vector result")
                embeddings.append([float(value) for value in vector])
        return embeddings
