from __future__ import annotations

import math
from collections import Counter

from app.retrieval.chunking import Chunk, tokenize


class BM25Index:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.tokenized = [tokenize(chunk.text + " " + chunk.title) for chunk in chunks]
        self.avgdl = sum(len(tokens) for tokens in self.tokenized) / max(len(self.tokenized), 1)
        self.doc_freq: Counter[str] = Counter()
        for tokens in self.tokenized:
            self.doc_freq.update(set(tokens))

    def search(self, query: str, top_k: int = 40) -> list[tuple[Chunk, float]]:
        query_tokens = tokenize(query)
        scores: list[tuple[Chunk, float]] = []
        total_docs = max(len(self.chunks), 1)
        for chunk, tokens in zip(self.chunks, self.tokenized):
            counts = Counter(tokens)
            score = 0.0
            for token in query_tokens:
                if token not in counts:
                    continue
                df = self.doc_freq[token]
                idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
                freq = counts[token]
                denom = freq + 1.5 * (1 - 0.75 + 0.75 * len(tokens) / max(self.avgdl, 1))
                score += idf * (freq * 2.5) / denom
            if score > 0:
                scores.append((chunk, round(score, 6)))
        return sorted(scores, key=lambda item: item[1], reverse=True)[:top_k]

