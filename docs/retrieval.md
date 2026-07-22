# Retrieval

Hybrid RAG uses three retrieval lanes:

- Chinese-aware BM25 recall using whole terms plus character bigrams and trigrams.
- Routed bge-m3 embeddings through a real OpenAI-compatible endpoint, with an explicit deterministic 1024-dimensional fake adapter in degraded/test mode.
- Persisted `Source-[:MENTIONS]->Entity` GraphRAG expansion with one-hop and two-hop neighbors.

When Neo4j is reachable, ingestion creates the `chunk_embedding` Vector Index and retrieval calls `db.index.vector.queryNodes`; GraphRAG expansion runs through Cypher. If Neo4j is unavailable, the service reports the reason and uses explicit in-memory vector/graph adapters.

Results are fused by reciprocal-rank fusion:

`score(d) = sum(1 / (k + rank_i(d)))`

Domain query expansion and lexical relevance reranking run after fusion. Final evidence records include source id, source type, title, excerpt, score, official flag, backend mode, expanded query, and retrieval explanation.
