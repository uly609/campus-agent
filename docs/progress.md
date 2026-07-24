git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
# CampusFlow AI Progress

Started: 2026-07-21

## Current Status

The workspace was empty at start. The starter pack instructions were read from `/Users/ntroi/Downloads/CampusFlow_AI_Codex_Starter_Pack`.

## Milestone Log

| Milestone | Status | Validation | Commit |
| --- | --- | --- | --- |
| M0 | Complete | `make lint` passed; `make typecheck` passed | Pending |
| M1 | Complete with external registry caveat | `make migrate` passed via SQLite fallback; `make seed` passed; `pytest backend/tests/unit/test_domain.py` passed; `make db-up` blocked by Docker Hub EOF pulling uncached Postgres/Neo4j | Pending |
| M2 | Complete | `pytest backend/tests/unit/test_chunking.py` passed; `pytest backend/tests/unit/test_rrf.py` passed; `pytest backend/tests/integration/test_retrieval.py` passed | Pending |
| M3 | Complete | `pytest backend/tests/integration/test_graph_rag.py` passed | Pending |
| M4 | Complete | `pytest backend/tests/unit/test_agent_graph.py` passed; `pytest backend/tests/integration/test_chat_flow.py` passed | Pending |
| M5 | Complete | `pytest backend/tests/unit/test_grounding.py` passed; `pytest backend/tests/unit/test_prompt_injection.py` passed | Pending |
| M6 | Complete | `pytest backend/tests/unit/test_llm_router.py` passed; `pytest backend/tests/integration/test_llm_cache.py` passed | Pending |
| M7 | Complete | `pytest backend/tests/unit/test_image_attributes.py` passed; `pytest backend/tests/unit/test_ocr_privacy.py` passed; `pytest backend/tests/integration/test_multimodal_search.py` passed | Pending |
| M8 | Complete | `pytest backend/tests/integration/test_post_draft_hitl.py` passed | Pending |
| M9 | Complete | `pytest backend/tests/unit/test_memory_conflict.py` passed; `pytest backend/tests/integration/test_memory_stream.py` passed | Pending |
| M10 | Complete | `cd frontend && npm run lint && npm run typecheck && npm run test` passed | Pending |
| M11 | Complete | `make eval` passed; persisted 80 intent, 18 retrieval, and 14 QA cases plus JSON/Markdown reports | Pending |
| M12 | Complete | `curl -f http://localhost:8000/metrics` passed; Prometheus, Grafana, and Alertmanager build from local configs and are healthy in Compose | Pending |
| M13 | Complete | `docker compose up --build -d` passed; all 8 services healthy; `make seed`, `make lint`, `make typecheck`, `make test`, `make eval`, `make e2e`, and `make smoke` passed | Pending |
| M14 | Complete | Compiled LangGraph, real HTTP providers, Neo4j Vector Index/GraphRAG, grounded-model validation, improved Chinese retrieval/evals; all final validations passed | Pending |
| M15 | Complete | Real Bailian Chat/Embedding/VLM calls passed; batched embeddings and provider-isolated offline validation passed | Pending |
| M16 | Complete | Vue 3 UI rebuild, real image upload, readable model output, responsive browser QA, and full regression validation passed | Pending |
| M17 | Complete | Knowledge ingestion, encrypted provider profiles, rate limiting, sessions, Vue admin surfaces, browser QA, and all stop-condition commands passed | Pending |

## 2026-07-21 M0 Notes

- Created repository contract files, dependency manifests, Compose topology, Dockerfiles, CI, frontend validation scripts, and documentation skeleton.
- Validation passed in Docker with explicit fake provider policy documented.

## 2026-07-21 M1 Notes

- Added SQLAlchemy metadata for posts, images, sessions, memories, eval runs, and traces.
- Added JSON repository and seed script generating 300 Chinese posts plus 30 official documents.
- Added demo token auth helper and base post CRUD API files.
- Docker Hub repeatedly returned EOF while pulling uncached `postgres:16-alpine` and `neo4j:5-community`; local SQLAlchemy validation used explicit SQLite fallback for `make migrate`.

## 2026-07-21 M2 Notes

- Implemented document parsing/chunking, BM25, deterministic bge-m3-compatible 1024-dimensional embeddings, Neo4j vector adapter, RRF, evidence schema, and retrieval explanations.
- Neo4j adapter attempts a real driver connection and reports explicit degraded in-memory vector mode when Neo4j is unavailable.
- Added `/app` to API `PYTHONPATH` so tests can import operational scripts.

## 2026-07-21 M3 Notes

- GraphRAG builds source/entity relationships for documents and posts, supports one-hop and two-hop expansion, contributes candidates to RRF, and exposes visualization data.
- LLM-style entity extraction is represented by the provider-compatible extraction path; without credentials the rule path is used explicitly.

## 2026-07-21 M4 Notes

- Implemented explicit AgentState, 13 node methods, six-stage workflow, conditional visual/greeting/tool/replan paths, tool registry, SSE events, and trace persistence.
- Fixed Redis fallback so unavailable Redis degrades to the explicit in-memory stream instead of timing out during tests.

## 2026-07-21 M5 Notes

- Added relevance judging, claim/evidence/citation enforcement, evidence-insufficient refusal, input/retrieval/output guardrails, PII filtering, and tool allowlisting.
- Prompt injection examples in English and Chinese are detected and retrieved content is marked as untrusted data.

## 2026-07-21 M6 Notes

- Added role-based chat, embedding, and VLM routing through local-primary, local-backup, and cloud-fallback tiers.
- Added Redis SETEX exact-match cache keys using role, model, prompt version, and input hash, with in-memory fallback when Redis is unavailable.
- Fake providers are explicit and used for tests/degraded local mode.

## 2026-07-21 M7 Notes

- Added fake Qwen2.5-VL-compatible image attribute extraction, image-enhanced query expansion, lost-and-found matching path, and synthetic-only student-card OCR.
- OCR privacy redacts names/student IDs and rejects non-demo card images.

## 2026-07-21 M8 Notes

- Added HITL draft sessions with VLM-derived fields, safety checks, version diffs, confirmation gate, and strict five-edit-round limit.
- Draft publishing requires explicit confirmation and a separate publish flag.

## 2026-07-21 M9 Notes

- Added Redis Stream memory producer/consumer, extraction, PII rejection, hash and embedding deduplication, conflict detection, supersedes, and user delete controls.
- When Redis is unavailable, memory uses the explicit in-memory stream adapter for local validation.

## 2026-07-21 M10 Notes

- Added a responsive demo UI with post feed, AI assistant with citations/traces, smart search, HITL draft assistant, memory management, eval dashboard, and trace page.
- Frontend validation is dependency-light and checks the required user-facing flows.

## 2026-07-21 M11 Notes

- Added eval runner that generates human-readable datasets if absent and computes metrics from actual predictions.
- Latest run wrote `evals/reports/latest.json` and `evals/reports/latest.md`; scores are computed, not hardcoded.

## 2026-07-21 M12 Notes

- Added 12 Prometheus metrics, Grafana dashboard config, Alertmanager rules, metrics middleware, and trace API.
- Validated `/metrics` on the running API service.

## 2026-07-21 M13 Notes

- Added README, architecture, agent flow, retrieval, memory, security, eval, API, and demo-script docs.
- Added E2E demo flow and smoke script.
- Final cleanup scan found no temporary markers, empty implementations, tautological tests, stub wording, or unexplained temporary code.
- Resolved Docker registry flakiness by using cached mirror images for Postgres and Neo4j, cached Redis, locally built frontend/Prometheus/Grafana images, and a locally built Alertmanager image from the official release archive.
- Fixed real-Redis validation issues by serializing memory stream fields as Redis-safe scalars and by scoping exact-match LLM cache keys to the provider tier.
- Final Compose validation passed on 2026-07-21: `docker compose up --build -d` succeeded and `docker compose ps --format json` reported healthy `api`, `web`, `postgres`, `redis`, `neo4j`, `prometheus`, `grafana`, and `alertmanager`.
- Final command validation passed after the healthy Compose run: `make seed`, `make lint`, `make typecheck`, `make test` (23 passed), `make eval` (`eval-7dfc3e46b9`, 80 intent / 18 retrieval / 14 QA cases), `make e2e` (backend E2E plus frontend tests), and `make smoke`.

## Degraded Mode Policy

External model credentials are optional for local demo and test runs. When absent, chat, embedding, and VLM providers use explicit fake adapters and include degraded-mode traces. PostgreSQL, Redis, and Neo4j are represented as real Docker Compose services for the full demo.

## 2026-07-22 M14 Notes

- Replaced the manual node loop with a compiled LangGraph `StateGraph` while preserving all 13 nodes, conditional branches, and the strict two-replan cap.
- Added tested OpenAI-compatible Chat, Embedding, and VLM adapters for local-primary, local-backup, and cloud-fallback tiers. Real model claims must cite supplied evidence ids and pass support validation.
- Added real Neo4j Vector Index queries and persisted `Source-[:MENTIONS]->Entity` Cypher expansion, retaining explicit in-memory degradation.
- Fixed Chinese tokenization, added domain query expansion and post-fusion reranking, diversified seed posts, and expanded official documents from 30 to 40.
- Replaced numbered intent copies with 80 distinct utterances, corrected relevance labels, added per-case reports, and removed hardcoded tool/cache/latency metrics.
- Final `eval-4d42b39c8f` computed: intent accuracy 1.0, Hit@8 1.0, Precision@5 1.0, Precision@8 0.9375, Recall@8 1.0, citation groundedness 1.0, refusal accuracy 1.0, and Judge F1 1.0.
- `docker compose up --build -d` passed with all eight services healthy. `make seed lint typecheck test eval e2e smoke` passed; 29 unit/integration tests and the E2E suite passed.

## 2026-07-22 M15 Notes

- Configured the ignored local `.env` for Bailian OpenAI-compatible cloud fallback: `qwen-plus`, `text-embedding-v3`, and `qwen-vl-plus`. Minimal real Chat, Embedding, and static-image VLM calls all completed without degraded mode.
- Added embedding batch support across the provider/router boundary and reused the retrieval service so the first real-model chat indexes the corpus efficiently.
- Isolated unit, integration, E2E, and eval commands from local provider credentials to keep validations deterministic and avoid unintended cloud charges. Runtime smoke continues to exercise the configured real providers.
- Final validation passed: 29 tests, lint, typecheck, `eval-acaa8777bf` (80 intent / 18 retrieval / 14 QA), E2E, frontend tests, and real-provider smoke. All eight Compose services are healthy.

## 2026-07-22 M16 Notes

- Replaced the static DOM-string renderer with a real Vue 3 Composition API application built by Vite, Lucide controls, and a reproducible multi-stage frontend Dockerfile.
- Removed raw JSON and provider debug fields from user-facing pages. Eval metrics, retrieval reasons, intents, image attributes, and model mode are presented with concise Chinese labels.
- Added real image selection, client-side resize/preview, same-origin Nginx API proxying, VLM attribute display, and complete HITL edit/confirm states.
- Normalized VLM values and scalar/list variations at the backend boundary so English provider output and string `location_hints` cannot break Chinese draft rendering.
- Browser QA passed for posts, real chat with citations, eight-result retrieval, synthetic image/VLM drafting, memory, latest eval report, and 50 trace records. Desktop and 390x844 mobile layouts had no horizontal overflow or console errors.
- Final validation passed with 31 unit/integration tests, E2E, frontend production build/tests, real-provider smoke, and all eight Compose services healthy. The verified Vite bundle is included for registry-independent Web image builds.

## 2026-07-24 M17 Notes

- Added managed knowledge documents with lifecycle status, SHA-256 content deduplication, Redis Streams ingestion events, progress, failure visibility, and a strict three-attempt retry cap.
- Added runtime Chat, Embedding, and VLM provider profiles ordered by local-primary, local-backup, and cloud-fallback tiers. API keys are Fernet-encrypted at rest and are never returned by public APIs.
- Added provider connectivity checks, Redis fixed-window API/chat rate limiting, and privacy-minimized session history that stores titles and counts instead of full message bodies.
- Added Vue knowledge-base, ingestion task, provider routing, and conversation management surfaces. Browser QA confirmed no raw JSON or encrypted credential fields, no console errors, and no horizontal overflow at 1280 desktop and 390x844 mobile viewports.
- `docker compose up --build -d` passed and all eight services reported healthy. `make seed`, `make lint`, `make typecheck`, `make test` (34 passed), `make eval` (`eval-6afc0d6cb2`, 80 intent / 18 retrieval / 14 QA), `make e2e` (2 backend flows plus frontend tests), and `make smoke` passed.
