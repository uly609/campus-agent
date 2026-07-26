from __future__ import annotations

from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]

from app.retrieval.chunking import Chunk, tokenize


class BM25Index:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.tokenized = [tokenize(chunk.text + " " + chunk.title) for chunk in chunks]
        self.index = BM25Okapi(self.tokenized)

    def search(self, query: str, top_k: int = 40) -> list[tuple[Chunk, float]]:
        query_tokens = tokenize(query)
        scores = self.index.get_scores(query_tokens)
        ranked = sorted(
            ((chunk, float(score)) for chunk, score in zip(self.chunks, scores) if score > 0),
            key=lambda item: item[1],
            reverse=True,
        )
        return ranked[:top_k]
