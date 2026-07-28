# Retrieval

Hybrid RAG uses three retrieval lanes:

- Chinese-aware BM25 recall through the maintained `rank-bm25` package, using whole terms plus character bigrams and trigrams.
- Routed embeddings through an OpenAI-compatible endpoint. The configured Bailian runtime uses `text-embedding-v3`; degraded/test mode uses an explicit deterministic 1024-dimensional bge-m3-compatible adapter.
- Persisted `Source-[:MENTIONS]->Entity` GraphRAG expansion with one-hop and two-hop neighbors.

When Neo4j is reachable, ingestion creates the `chunk_embedding` Vector Index and retrieval calls `db.index.vector.queryNodes`; GraphRAG expansion runs through Cypher. If Neo4j is unavailable, the service reports the reason and uses explicit in-memory vector/graph adapters.

Each Neo4j chunk stores the embedding-model signature. On API restart, the retrieval service reuses the persisted vectors when every corpus chunk matches the active model; corpus embedding runs again only when the corpus or model changes.

Results are fused by reciprocal-rank fusion:

`score(d) = sum(1 / (k + rank_i(d)))`

Domain query expansion runs before retrieval. After RRF fusion, the configured Bailian runtime sends up to 60 candidates to `qwen3-rerank`; deployments without reranker credentials report degraded mode and use an explicit lexical fallback. Query-facet detection distinguishes physical location, time, and non-physical lookup wording such as `在哪里看`, and rejects same-topic evidence that does not express the requested answer type even when the model gives it a high relevance score. Grounded synthesis uses minimal sufficient evidence and removes duplicate excerpts and claims before returning citations.

Final evidence records include source id, source type, title, excerpt, score, official flag, backend mode, expanded query, facet match, and retrieval explanation.


## Corrective official-web retrieval

Local Hybrid RAG remains the primary source. If the relevance gate cannot find sufficient evidence, the first replan rewrites the query and searches local official documents plus community posts. The second and final replan can call a Tavily-compatible search endpoint restricted by `OFFICIAL_WEB_ALLOWED_DOMAINS`. Without an endpoint, credential, and domain allowlist, the tool returns `OFFICIAL_WEB_SEARCH_NOT_CONFIGURED`; it does not fabricate web results.

Grounded model output must bind each Claim to an Evidence id and copy an exact `quoted_span` from that Evidence. Unknown evidence, invented quotations, unsupported facets, or insufficient evidence lead to fallback grounded synthesis or refusal.
