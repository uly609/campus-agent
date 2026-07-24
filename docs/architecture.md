git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
# Architecture

CampusFlow AI is organized around the agent, not the web framework.

- FastAPI exposes chat, post, ingest, memory, eval, health, and metrics endpoints.
- A compiled LangGraph `StateGraph` owns the 13-node, six-stage workflow and emits node/tool/replan/citation trace events.
- Retrieval combines Chinese n-gram BM25, routed bge-m3 embeddings, Neo4j Vector Index queries, persisted Neo4j GraphRAG relationships, query expansion, relevance reranking, and RRF.
- Chat, embedding, and VLM providers use OpenAI-compatible HTTP adapters at local-primary, local-backup, and cloud-fallback tiers. Missing credentials use explicit fake adapters.
- Runtime provider profiles join the same three-tier router. Credentials are Fernet-encrypted at rest, redacted from API responses, and checked through the provider model-list endpoint.
- Knowledge documents move through queued, indexing, ready, or failed states. Redis Streams record jobs while bounded workers perform deduplication, chunking, embedding, Neo4j indexing, and retry tracking.
- Redis fixed-window limits protect API and chat endpoints. Session records retain only a short title, count, and timestamps rather than full message bodies.
- Real-model grounded synthesis accepts only structured claims that cite supplied evidence ids and pass support validation; invalid output falls back to deterministic grounded synthesis.
- Long-term memory is written as Redis Stream events, extracted, deduplicated, conflict-checked, and stored for user control.
- Vue demo pages exercise the actual API flows.

External model outputs are never required for local validation. External retrieved data is treated as untrusted data, not instructions, and provider keys are never logged.
