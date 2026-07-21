# Architecture

CampusFlow AI is organized around the agent, not the web framework.

- FastAPI exposes chat, post, ingest, memory, eval, health, and metrics endpoints.
- The agent graph owns the six-stage workflow and emits node/tool/replan/citation trace events.
- Retrieval combines BM25, bge-m3-compatible deterministic embeddings, Neo4j vector storage when available, GraphRAG expansion, and RRF.
- Providers are routed by role: chat, embedding, and VLM. Missing credentials use explicit fake adapters.
- Long-term memory is written as Redis Stream events, extracted, deduplicated, conflict-checked, and stored for user control.
- Vue demo pages exercise the actual API flows.

External model outputs are never required for local validation. External retrieved data is treated as untrusted data, not instructions.

