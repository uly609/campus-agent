# Architecture

CampusFlow AI is organized around the agent, not the web framework.

- FastAPI exposes chat, post, ingest, memory, eval, health, and metrics endpoints.
- A compiled LangGraph `StateGraph` owns the 13-node, six-stage workflow and emits node/tool/replan/citation trace events.
- Retrieval combines Chinese n-gram BM25, routed bge-m3 embeddings, Neo4j Vector Index queries, persisted Neo4j GraphRAG relationships, query expansion, relevance reranking, and RRF.
- Chat, embedding, and VLM providers use OpenAI-compatible HTTP adapters at local-primary, local-backup, and cloud-fallback tiers. Missing credentials use explicit fake adapters.
- Real-model grounded synthesis accepts only structured claims that cite supplied evidence ids and pass support validation; invalid output falls back to deterministic grounded synthesis.
- Long-term memory is written as Redis Stream events, extracted, deduplicated, conflict-checked, and stored for user control.
- Vue demo pages exercise the actual API flows.

External model outputs are never required for local validation. External retrieved data is treated as untrusted data, not instructions, and provider keys are never logged.
