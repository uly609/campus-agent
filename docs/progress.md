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
| M12 | Complete with external registry caveat | `curl -f http://localhost:8000/metrics` passed against API service; Prometheus/Grafana/Alertmanager configs present; full service health still awaits external image pulls | Pending |
| M13 | Locally complete; full Compose blocked | `make seed`, `make lint`, `make typecheck`, `make test`, `make eval`, `make e2e`, and `make smoke` passed; `docker compose up --build -d` blocked by Docker Hub EOF for uncached Neo4j/Postgres/Alertmanager images | Pending |

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
- Final local validation passed: `make seed`, `make lint`, `make typecheck`, `make test`, `make eval`, `make e2e`, and `make smoke`.
- Full `docker compose up --build -d` is not yet satisfied because Docker Hub repeatedly returns EOF/auth errors for uncached `neo4j:5-community`, `postgres:16-alpine`, and `prom/alertmanager:v0.27.0`.

## Degraded Mode Policy

External model credentials are optional for local demo and test runs. When absent, chat, embedding, and VLM providers use explicit fake adapters and include degraded-mode traces. PostgreSQL, Redis, and Neo4j are represented as real Docker Compose services for the full demo.
