# PLAN.md - CampusFlow AI Implementation Plan

Every milestone requires validation, failure fixes, status updates here, `docs/progress.md`, and an atomic commit.

## Overall Stop Conditions

- [x] Docker Compose all required services healthy.
- [x] `make seed`, `make lint`, `make typecheck`, `make test`, `make eval`, `make e2e`, and `make smoke` pass.
- [x] Agent, RAG, GraphRAG, VLM/OCR adapter, HITL, memory, fallback, and observability have runnable code and tests.
- [x] Vue 3 demo can complete core flows.
- [x] README and demo script are actionable for a new user.

## M0 - Repository And Engineering Standards

- [x] Complete directory structure.
- [x] Python, Vue, Docker, lint, typecheck, and test configuration.
- [x] `.env.example`.
- [x] Makefile.
- [x] GitHub Actions.
- [x] `docs/progress.md`.
- [x] Dependencies pinned to reasonable ranges.

Validation:

```bash
make lint
make typecheck
```

## M1 - Data Model, Database, And Seed Data

- [x] PostgreSQL / SQLAlchemy / Alembic definitions.
- [x] Post, PostImage, UserSession, Memory, EvalRun, and Trace tables.
- [x] At least 300 Chinese campus posts.
- [x] At least 30 campus documents.
- [x] API CRUD.
- [x] Demo token auth.

Validation:

```bash
make db-up
make migrate
make seed
pytest backend/tests/unit/test_domain.py
```

## M2 - Document Ingestion And Hybrid Retrieval

- [x] Document parsing.
- [x] Chunking.
- [x] BM25.
- [x] Embedding provider.
- [x] Neo4j vector index.
- [x] RRF.
- [x] Evidence schema.
- [x] Retrieval explanations.

Validation:

```bash
pytest backend/tests/unit/test_chunking.py
pytest backend/tests/unit/test_rrf.py
pytest backend/tests/integration/test_retrieval.py
```

## M3 - GraphRAG

- [x] Document -> Chunk -> Entity graph.
- [x] Post, Topic, Location, Event graph relationships.
- [x] Rule-based and LLM-based entity extraction paths.
- [x] One-hop and two-hop expansion.
- [x] Graph candidates fused with BM25/vector.
- [x] Graph visualization API.

Validation:

```bash
pytest backend/tests/integration/test_graph_rag.py
```

## M4 - LangGraph Main Agent

- [x] AgentState.
- [x] 13 nodes.
- [x] Six-stage main flow.
- [x] Conditional edges.
- [x] Replan.
- [x] Tool Registry.
- [x] Checkpoint.
- [x] SSE events.
- [x] Fake LLM tests.

Validation:

```bash
pytest backend/tests/unit/test_agent_graph.py
pytest backend/tests/integration/test_chat_flow.py
```

## M5 - Grounded Synthesis And Safety

- [x] Relevance Judge.
- [x] Claim-evidence binding.
- [x] Citations.
- [x] Evidence-insufficient refusal.
- [x] Three-layer prompt injection defense.
- [x] PII filtering.
- [x] Tool allowlist.
- [x] Safety audit logs.

Validation:

```bash
pytest backend/tests/unit/test_grounding.py
pytest backend/tests/unit/test_prompt_injection.py
```

## M6 - Model Routing, Fallback, And Cache

- [x] Chat, embedding, and VLM roles.
- [x] Local primary, local backup, cloud fallback.
- [x] Fallback only on recoverable infrastructure errors.
- [x] Redis SETEX exact cache.
- [x] Provider trace.
- [x] Fake providers.
- [x] Timeout and retry.

Validation:

```bash
pytest backend/tests/unit/test_llm_router.py
pytest backend/tests/integration/test_llm_cache.py
```

## M7 - VLM, Image Search, And OCR

- [x] Image attribute extraction.
- [x] Image-enhanced query.
- [x] Lost-and-found matching.
- [x] Synthetic student-card OCR demo.
- [x] Privacy protection.
- [x] Explicit fake VLM adapter without keys.
- [x] Image upload/search API.

Validation:

```bash
pytest backend/tests/unit/test_image_attributes.py
pytest backend/tests/unit/test_ocr_privacy.py
pytest backend/tests/integration/test_multimodal_search.py
```

## M8 - AI Post Draft Subgraph And HITL

- [x] VLM analysis.
- [x] Draft generation.
- [x] Content safety check.
- [x] Interrupt-style user confirmation.
- [x] Five edit rounds.
- [x] Version diff.
- [x] Publish only after confirmation.

Validation:

```bash
pytest backend/tests/integration/test_post_draft_hitl.py
```

## M9 - Long-Term Memory

- [x] Redis Streams producer.
- [x] Consumer group.
- [x] Memory extractor.
- [x] Hash and embedding deduplication.
- [x] Conflict detection.
- [x] Supersedes.
- [x] Event expiry.
- [x] User view/delete/disable.

Validation:

```bash
pytest backend/tests/unit/test_memory_conflict.py
pytest backend/tests/integration/test_memory_stream.py
```

## M10 - Vue 3 Demo UI

- [x] Post feed.
- [x] AI assistant.
- [x] Smart search.
- [x] Post drafting assistant.
- [x] Memory management.
- [x] Eval dashboard.
- [x] Trace page.
- [x] Responsive loading, error, and empty states.

Validation:

```bash
cd frontend && npm run lint && npm run typecheck && npm run test
```

## M11 - Eval

- [x] 80 intent cases.
- [x] 18 retrieval cases.
- [x] 14 QA cases.
- [x] Graders.
- [x] JSON and Markdown reports.
- [x] Prompt/model versions.
- [x] Paired comparison.
- [x] No hardcoded scores.

Validation:

```bash
make eval
```

## M12 - Prometheus, Grafana, And Alerts

- [x] 12 metrics.
- [x] Grafana dashboard.
- [x] Alertmanager rules.
- [x] OpenTelemetry-style trace ids.
- [x] Trace API and frontend page.

Validation:

```bash
curl -f http://localhost:8000/metrics
```

## M13 - E2E, Docker, Docs, And Final Review

- [x] Docker health checks.
- [x] E2E flows.
- [x] README.
- [x] Architecture docs.
- [x] Agent flow docs.
- [x] Retrieval docs.
- [x] Memory docs.
- [x] Security docs.
- [x] Eval docs.
- [x] API docs.
- [x] Demo script.
- [x] Clean temporary code.
- [x] Final safety and dependency scan.

Validation:

```bash
docker compose up --build -d
make seed
make lint
make typecheck
make test
make eval
make e2e
make smoke
```

## M14 - Agent Fidelity And Evaluation Hardening

- [x] Replace manual orchestration with compiled LangGraph `StateGraph` execution.
- [x] Add real OpenAI-compatible Chat, Embedding, and VLM providers with bounded fallback.
- [x] Route embeddings through provider/cache infrastructure.
- [x] Query the Neo4j Vector Index and persisted GraphRAG relationships.
- [x] Validate real-model claims against supplied evidence ids.
- [x] Add Chinese query expansion, tokenization, and relevance reranking.
- [x] Replace duplicated intent templates and correct retrieval/QA relevance labels.
- [x] Compute Judge F1, citation groundedness, retrieval precision/recall, cache hits, and latency from executions.
- [x] Make Docker builds independent of ignored local binaries and reduce build context.
- [x] Run all stop-condition commands with eight healthy services.
