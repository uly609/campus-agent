from __future__ import annotations

from app.domain.schemas import Evidence
from app.retrieval.bm25 import BM25Index
from app.retrieval.chunking import Chunk, tokenize
from app.retrieval.graph_rag import GraphRAG, extract_entities
from app.retrieval.neo4j_store import Neo4jVectorStore, VectorRecord
from app.retrieval.query_expansion import expand_campus_query
from app.retrieval.query_facets import query_facet, text_matches_query_facet
from app.retrieval.reranker import RetrievalReranker
from app.retrieval.routed_embeddings import RoutedEmbeddingProvider
from app.retrieval.rrf import reciprocal_rank_fusion


class RetrievalService:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.embedding_provider = RoutedEmbeddingProvider()
        self.bm25 = BM25Index(chunks)
        self.graph = GraphRAG(chunks)
        self.vector_store = Neo4jVectorStore()
        self.reranker = RetrievalReranker()
        self._indexed = False

    async def rebuild(self) -> None:
        if self.vector_store.reuse_persisted_chunks(
            self.chunks,
            self.embedding_provider.model_name,
        ):
            self._indexed = True
            return
        embeddings = await self.embedding_provider.embed([chunk.text for chunk in self.chunks])
        self.vector_store.upsert_chunks(
            [VectorRecord(chunk=chunk, embedding=embedding) for chunk, embedding in zip(self.chunks, embeddings)],
            self.embedding_provider.model_name,
        )
        self.vector_store.upsert_graph()
        self._indexed = True

    async def search(self, query: str, top_k: int = 12) -> list[Evidence]:
        if not self._indexed:
            await self.rebuild()
        expanded_query = expand_campus_query(query)
        query_embedding = (await self.embedding_provider.embed([expanded_query]))[0]
        bm25_results = self.bm25.search(expanded_query, top_k=40)
        vector_results = self.vector_store.vector_search(query_embedding, top_k=40)
        graph_results = self.vector_store.graph_search(extract_entities(expanded_query), top_k=20)
        if not graph_results:
            graph_results = self.graph.expand(expanded_query, top_k=20)
        fused = reciprocal_rank_fusion(
            [
                [(chunk.source_id, (chunk, score, "bm25")) for chunk, score in bm25_results],
                [(chunk.source_id, (chunk, score, "vector")) for chunk, score in vector_results],
                [(chunk.source_id, (chunk, score, "graph")) for chunk, score in graph_results],
            ]
        )
        direct_query_tokens = set(tokenize(query))
        expanded_query_tokens = set(tokenize(expanded_query))
        facet = query_facet(query)

        def rerank_score(item: tuple[str, float, tuple[Chunk, float, str]]) -> float:
            chunk = item[2][0]
            candidate_text = f"{chunk.title} {chunk.text}"
            candidate_tokens = set(tokenize(candidate_text))
            direct_overlap = len(direct_query_tokens.intersection(candidate_tokens)) / max(len(direct_query_tokens), 1)
            expanded_overlap = len(expanded_query_tokens.intersection(candidate_tokens)) / max(
                len(expanded_query_tokens), 1
            )
            facet_adjustment = 0.2 if facet and text_matches_query_facet(query, candidate_text) else 0.0
            if facet and not text_matches_query_facet(query, candidate_text):
                facet_adjustment = -0.2
            official_boost = 0.08 if chunk.official and expanded_query != query else 0.0
            return item[1] + direct_overlap + expanded_overlap * 0.35 + facet_adjustment + official_boost

        candidate_rows = sorted(fused, key=rerank_score, reverse=True)[:60]
        community_ranked = await self.reranker.rerank(
            query,
            [payload[0] for _, _, payload in candidate_rows],
            top_k,
        )
        evidence = []
        for index, ranked in enumerate(community_ranked, start=1):
            chunk = ranked.chunk
            source_id = chunk.source_id
            final_score = max(0.0, min(1.0, ranked.score))
            evidence.append(
                Evidence(
                    evidence_id=f"ev-{index}-{source_id}",
                    source_id=source_id,
                    source_type="official" if chunk.official else "post",
                    title=chunk.title,
                    excerpt=chunk.text[:360],
                    score=round(final_score, 6),
                    official=chunk.official,
                    metadata={
                        **chunk.metadata,
                        "retrieval": f"rank-bm25+neo4j-vector+graphrag+rrf+{ranked.mode}",
                        "rerank_model": ranked.mode,
                        "rerank_degraded_reason": self.reranker.degraded_reason,
                        "expanded_query": expanded_query,
                        "neo4j_mode": "real" if not self.vector_store.degraded_reason else "degraded-memory",
                        "query_facet": facet or "general",
                        "facet_match": text_matches_query_facet(query, f"{chunk.title} {chunk.text}"),
                        "explanation": (
                            f"Returned because query terms, graph entities, and the {facet or 'general'} "
                            f"question facet overlap with {chunk.title}."
                        ),
                    },
                )
            )
        return evidence
