# Retrieval

Hybrid RAG uses three retrieval lanes:

- Chinese-aware BM25 recall using whole terms plus character bigrams and trigrams.
- Routed embeddings through an OpenAI-compatible endpoint. The configured Bailian runtime uses `text-embedding-v3`; degraded/test mode uses an explicit deterministic 1024-dimensional bge-m3-compatible adapter.
- Persisted `Source-[:MENTIONS]->Entity` GraphRAG expansion with one-hop and two-hop neighbors.

When Neo4j is reachable, ingestion creates the `chunk_embedding` Vector Index and retrieval calls `db.index.vector.queryNodes`; GraphRAG expansion runs through Cypher. If Neo4j is unavailable, the service reports the reason and uses explicit in-memory vector/graph adapters.

Results are fused by reciprocal-rank fusion:

`score(d) = sum(1 / (k + rank_i(d)))`

Domain query expansion and lexical relevance reranking run after fusion. Query-facet detection distinguishes location and time questions, boosts evidence that answers the requested facet, and rejects same-topic evidence that answers a different facet. Grounded synthesis uses minimal sufficient evidence and removes duplicate excerpts and claims before returning citations.

Final evidence records include source id, source type, title, excerpt, score, official flag, backend mode, expanded query, facet match, and retrieval explanation.
