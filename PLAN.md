# PLAN.md - CampusFlow AI Implementation Plan

Every milestone requires validation, failure fixes, status updates here, `docs/progress.md`, and an atomic commit.

## Overall Stop Conditions

- [ ] Docker Compose all required services healthy.
- [ ] `make seed`, `make lint`, `make typecheck`, `make test`, `make eval`, `make e2e`, and `make smoke` pass.
- [ ] Agent, RAG, GraphRAG, VLM/OCR adapter, HITL, memory, fallback, and observability have runnable code and tests.
- [ ] Vue 3 demo can complete core flows.
- [ ] README and demo script are actionable for a new user.

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

- [ ] Document parsing.
- [ ] Chunking.
- [ ] BM25.
- [ ] Embedding provider.
- [ ] Neo4j vector index.
- [ ] RRF.
- [ ] Evidence schema.
- [ ] Retrieval explanations.

Validation:

```bash
pytest backend/tests/unit/test_chunking.py
pytest backend/tests/unit/test_rrf.py
pytest backend/tests/integration/test_retrieval.py
```

## M3 - GraphRAG

- [ ] Document -> Chunk -> Entity graph.
- [ ] Post, Topic, Location, Event graph relationships.
- [ ] Rule-based and LLM-based entity extraction paths.
- [ ] One-hop and two-hop expansion.
- [ ] Graph candidates fused with BM25/vector.
- [ ] Graph visualization API.

Validation:

```bash
pytest backend/tests/integration/test_graph_rag.py
```

## M4 - LangGraph Main Agent

- [ ] AgentState.
- [ ] 13 nodes.
- [ ] Six-stage main flow.
- [ ] Conditional edges.
- [ ] Replan.
- [ ] Tool Registry.
- [ ] Checkpoint.
- [ ] SSE events.
- [ ] Fake LLM tests.

Validation:

```bash
pytest backend/tests/unit/test_agent_graph.py
pytest backend/tests/integration/test_chat_flow.py
```

## M5 - Grounded Synthesis And Safety

- [ ] Relevance Judge.
- [ ] Claim-evidence binding.
- [ ] Citations.
- [ ] Evidence-insufficient refusal.
- [ ] Three-layer prompt injection defense.
- [ ] PII filtering.
- [ ] Tool allowlist.
- [ ] Safety audit logs.

Validation:

```bash
pytest backend/tests/unit/test_grounding.py
pytest backend/tests/unit/test_prompt_injection.py
```

## M6 - Model Routing, Fallback, And Cache

- [ ] Chat, embedding, and VLM roles.
- [ ] Local primary, local backup, cloud fallback.
- [ ] Fallback only on recoverable infrastructure errors.
- [ ] Redis SETEX exact cache.
- [ ] Provider trace.
- [ ] Fake providers.
- [ ] Timeout and retry.

Validation:

```bash
pytest backend/tests/unit/test_llm_router.py
pytest backend/tests/integration/test_llm_cache.py
```

## M7 - VLM, Image Search, And OCR

- [ ] Image attribute extraction.
- [ ] Image-enhanced query.
- [ ] Lost-and-found matching.
- [ ] Synthetic student-card OCR demo.
- [ ] Privacy protection.
- [ ] Explicit fake VLM adapter without keys.
- [ ] Image upload/search API.

Validation:

```bash
pytest backend/tests/unit/test_image_attributes.py
pytest backend/tests/unit/test_ocr_privacy.py
pytest backend/tests/integration/test_multimodal_search.py
```

## M8 - AI Post Draft Subgraph And HITL

- [ ] VLM analysis.
- [ ] Draft generation.
- [ ] Content safety check.
- [ ] Interrupt-style user confirmation.
- [ ] Five edit rounds.
- [ ] Version diff.
- [ ] Publish only after confirmation.

Validation:

```bash
pytest backend/tests/integration/test_post_draft_hitl.py
```

## M9 - Long-Term Memory

- [ ] Redis Streams producer.
- [ ] Consumer group.
- [ ] Memory extractor.
- [ ] Hash and embedding deduplication.
- [ ] Conflict detection.
- [ ] Supersedes.
- [ ] Event expiry.
- [ ] User view/delete/disable.

Validation:

```bash
pytest backend/tests/unit/test_memory_conflict.py
pytest backend/tests/integration/test_memory_stream.py
```

## M10 - Vue 3 Demo UI

- [ ] Post feed.
- [ ] AI assistant.
- [ ] Smart search.
- [ ] Post drafting assistant.
- [ ] Memory management.
- [ ] Eval dashboard.
- [ ] Trace page.
- [ ] Responsive loading, error, and empty states.

Validation:

```bash
cd frontend && npm run lint && npm run typecheck && npm run test
```

## M11 - Eval

- [ ] 80 intent cases.
- [ ] 18 retrieval cases.
- [ ] 14 QA cases.
- [ ] Graders.
- [ ] JSON and Markdown reports.
- [ ] Prompt/model versions.
- [ ] Paired comparison.
- [ ] No hardcoded scores.

Validation:

```bash
make eval
```

## M12 - Prometheus, Grafana, And Alerts

- [ ] 12 metrics.
- [ ] Grafana dashboard.
- [ ] Alertmanager rules.
- [ ] OpenTelemetry-style trace ids.
- [ ] Trace API and frontend page.

Validation:

```bash
curl -f http://localhost:8000/metrics
```

## M13 - E2E, Docker, Docs, And Final Review

- [ ] Docker health checks.
- [ ] E2E flows.
- [ ] README.
- [ ] Architecture docs.
- [ ] Agent flow docs.
- [ ] Retrieval docs.
- [ ] Memory docs.
- [ ] Security docs.
- [ ] Eval docs.
- [ ] API docs.
- [ ] Demo script.
- [ ] Clean temporary code.
- [ ] Final safety and dependency scan.

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
