# Retrieval

Hybrid RAG uses three retrieval lanes:

- BM25 keyword recall.
- bge-m3-compatible 1024-dimensional deterministic embeddings.
- GraphRAG entity expansion with one-hop and two-hop neighbors.

Neo4j vector storage is attempted when configured and reachable. If unavailable, the service reports `neo4j_unavailable:*` and uses an explicit in-memory vector store for local demo validation.

Results are fused by reciprocal-rank fusion:

`score(d) = sum(1 / (k + rank_i(d)))`

Final evidence records include source id, source type, title, excerpt, score, official flag, and retrieval explanation.

