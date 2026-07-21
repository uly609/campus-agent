from __future__ import annotations

from app.domain.schemas import Evidence
from app.retrieval.bm25 import BM25Index
from app.retrieval.chunking import Chunk
from app.retrieval.embeddings import DeterministicBgeM3CompatibleEmbedding
from app.retrieval.graph_rag import GraphRAG
from app.retrieval.neo4j_store import Neo4jVectorStore, VectorRecord
from app.retrieval.rrf import reciprocal_rank_fusion


class RetrievalService:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.embedding_provider = DeterministicBgeM3CompatibleEmbedding()
        self.bm25 = BM25Index(chunks)
        self.graph = GraphRAG(chunks)
        self.vector_store = Neo4jVectorStore()
        self._indexed = False

    async def rebuild(self) -> None:
        embeddings = await self.embedding_provider.embed([chunk.text for chunk in self.chunks])
        self.vector_store.upsert_chunks(
            [VectorRecord(chunk=chunk, embedding=embedding) for chunk, embedding in zip(self.chunks, embeddings)]
        )
        self._indexed = True

    async def search(self, query: str, top_k: int = 12) -> list[Evidence]:
        if not self._indexed:
            await self.rebuild()
        query_embedding = (await self.embedding_provider.embed([query]))[0]
        bm25_results = self.bm25.search(query, top_k=40)
        vector_results = self.vector_store.vector_search(query_embedding, top_k=40)
        graph_results = self.graph.expand(query, top_k=20)
        fused = reciprocal_rank_fusion(
            [
                [(chunk.source_id, (chunk, score, "bm25")) for chunk, score in bm25_results],
                [(chunk.source_id, (chunk, score, "vector")) for chunk, score in vector_results],
                [(chunk.source_id, (chunk, score, "graph")) for chunk, score in graph_results],
            ]
        )
        evidence = []
        for index, (source_id, fused_score, payload) in enumerate(fused[:top_k], start=1):
            chunk = payload[0]
            evidence.append(
                Evidence(
                    evidence_id=f"ev-{index}-{source_id}",
                    source_id=source_id,
                    source_type="official" if chunk.official else "post",
                    title=chunk.title,
                    excerpt=chunk.text[:360],
                    score=round(fused_score, 6),
                    official=chunk.official,
                    metadata={
                        **chunk.metadata,
                        "retrieval": "bm25+vector+graph+rrf",
                        "neo4j_mode": "real" if not self.vector_store.degraded_reason else "degraded-memory",
                        "explanation": f"Returned because query terms and graph entities overlap with {chunk.title}.",
                    },
                )
            )
        return evidence

