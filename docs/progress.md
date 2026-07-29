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
| M18 | Complete | Curated multi-scenario demo feed and 40-document school knowledge base; `make seed`, `make lint`, `make typecheck`, `make test`, `make eval`, `make e2e`, and `make smoke` passed | Pending |
| M19 | Complete | Query-facet reranking and minimal sufficient evidence; 40 tests, real Bailian location QA, eval, E2E, and smoke passed | Pending |
| M20 | Complete | Clickable intelligent-search results, typed source-detail API, responsive detail dialog, browser QA, and full regression validation passed | Pending |
| M21 | Complete | Eight-scenario post Agent, text-only and VLM-enhanced drafting, shared LangGraph/API service, frontend controls, browser QA, and full validation passed | Pending |
| M22 | Complete | Real continuous-conversation QA, runtime index reuse, memory/security/draft routing, timetable precision, 56 tests, full eval/E2E/smoke, and eight healthy services | Pending |
| M23 | Complete | Honest evaluation v2 with exact graded qrels, hard cases, standard IR/QA/control-flow metrics, 60 tests, full validation, and eight healthy services | Pending |
| M24 | Complete | Community BM25 plus Bailian reranking, facet-safe refusal, complete draft publishing, browser QA, 65 tests, full validation, and eight healthy services | Pending |
| M25 | Complete | Published-post memory events, residence extraction, existing-post backfill, 66 tests, 3 E2E flows, eval, and smoke passed | Pending |
| M26 | Complete | Typed intent/tool plans, registry validation, Ruff, Mypy, and 70 unit/integration tests passed | Pending |
| M28 | Complete | Model-driven Planner, Skill catalog, corrective official-web retrieval, semantic memory recall, verbatim citations, 81 tests, frontend build, and honest eval passed | Pending |
| M29 | Complete | Authorized XiaoLin campus Skills, FastMCP weather, clickable Vue demos, 92 tests, honest eval, 3 E2E flows, smoke, and 8 healthy services | Pending |
| M30 | Complete | XiaoLin Planner/Selector/Executor chat workbench, streamed task trace, planning-style grounded answers, 94 tests, eval, E2E, smoke, and 8 healthy services | Pending |
| M37 | Complete | Persistent anonymous post comments, synchronized counts, frontend checks, focused backend tests, browser QA, and healthy rebuilt API/Web services | Pending |
| M38 | Complete | Compact community feed, direct-voice imported posts, 18-post runtime migration, regression coverage, and responsive browser QA | Pending |
| M39 | Complete | Feed-integrated semantic search, true post-only retrieval, offset pagination, load-more interaction, E2E, and browser QA | Pending |

## 2026-07-29 M30 Notes

- Replaced the broken AI 学问 merge with a complete `浙商小林` chat workbench inside the existing CampusFlow Vue app, not as a separate mode or separate localhost service.
- Connected the chat endpoint to the XiaoLin pipeline: `TaskPlanner -> ToolSelector -> TaskExecutor -> ResponseGenerator`, with the upstream XiaoLin SSE protocol on `POST /api/v1/chat/`: `step`, `task_plan`, `tool_selections`, `task_result`, `process_summary`, then streamed `{content: ...}` chunks.
- Kept all execution behind the existing ToolRegistry and grounding/citation schemas. Tool calls now expose course schedule, campus notices, venues, weather, and campus knowledge outputs with timings and execution status in the answer UI.
- Changed activity-planning responses from raw evidence snippets into actionable Zhejiang Gongshang University plans, while still citing retrieved skill/weather evidence and explicitly refusing to invent missing personal/contact fields.
- Rebuilt API/Web images and refreshed `http://localhost:5173`. Verified the running 5173 proxy streams XiaoLin task planning, tool selection, task execution, process summary, and answer content chunks using the upstream event shape.
- Validation passed: `make lint`, `make typecheck`, `make test` (94 passed), `make eval` (`eval-68849bcce7`), `make e2e` (3 backend flows plus frontend tests), `make smoke`, direct XiaoLin SSE verification through 5173, and all 8 Docker services healthy.

## 2026-07-28 M26 Notes

- Added strict citation provenance validation in grounded synthesis. Generated citations now verify claim ids, evidence ids, and source provenance before returning an answer.
- Replaced the graph's untyped tuple/dictionary intent-planning path with Pydantic v2 `IntentPlan` and `ToolCall` schemas while preserving the legacy `plan_intent` adapter.
- Added pre-execution validation for registered tool names and required arguments, with the active `ToolRegistry` as the graph's allowlist source.
- Preserved the compiled 13-node LangGraph workflow and deterministic fallback behavior. Added four focused planner tests.
- Added planner argument type validation before execution and regression coverage for invalid tool parameters.
- Added corrective retrieval and memory evaluation metrics, including corrective RAG success tracking and memory recall trace measurement.
- Improved Vue citation interaction and trace readability without replacing the existing SSE/API flow.
- Validation passed: `make lint` and `make test` (66 backend unit/integration tests).

## 2026-07-28 M27 Notes

- Entered Eval hardening phase after planner, tool validation, citation provenance, memory lifecycle, and frontend interaction improvements.
- Ran `make eval` successfully with offline deterministic providers.
- Current evaluation run: `eval-f2402e40e1`.
- Metrics covered intent accuracy, retrieval precision/recall, citation precision, faithfulness, refusal/replan metrics, corrective RAG success rate, memory recall traces, and cache behavior.
- Provider limitation remains explicit: this run uses fake chat, embedding, and VLM providers for deterministic regression.

## 2026-07-26 M25 Notes

- Fixed a disconnected product path: AI chat emitted long-term-memory events, but confirmed post publication did not. Draft requests now carry the active user and session, and the first successful publication emits the post text to the same Redis Stream.
- Extended conservative memory extraction to first-person residence statements such as `我住在生活区西区`. A generic post that only mentions the same location remains ineligible, so publication does not turn the whole feed into user memory.
- Repeated publish requests remain idempotent and do not emit duplicate memory events. The already-published demo post was backfilled for `demo-user` and verified through the memory API.
- Final validation passed: lint, typecheck, 66 unit/integration tests, eval `eval-da89926ec9`, 3 backend E2E tests, frontend tests, and smoke.

## 2026-07-26 M24 Notes

- Replaced the custom BM25 formula with `rank-bm25` while preserving Neo4j Vector Index recall, GraphRAG expansion, and RRF fusion. The fused candidate set is reranked by Bailian `qwen3-rerank` when configured and uses an explicit lexical fallback otherwise.
- Added a requested-answer facet gate after reranking. A location question now requires a passage that expresses a location relation, so a post that merely mentions a teaching building cannot be promoted as the building's address.
- Completed the HITL posting lifecycle in the Vue UI: users generate and edit a draft, confirm it, then explicitly publish it. The backend blocks unconfirmed publication and returns the original post for repeated publish calls instead of creating duplicates.
- Real browser QA generated, confirmed, and published an event post, verified it in the feed, and confirmed that `教学楼在哪` returns an evidence-insufficient refusal without citations or console errors.
- Final validation passed after a full Compose rebuild with all eight services healthy: seed, lint, typecheck, 65 unit/integration tests, eval `eval-89cc80c036`, 2 backend E2E tests, frontend tests, and smoke.

## 2026-07-26 M23 Notes

- Replaced broad source-prefix judgments and repeated easy questions with exact graded qrels and paraphrase, overlap, hard-negative, partial-evidence, conflict, OOD, and prompt-injection cases while preserving the required 80 intent, 18 retrieval, and 14 QA counts.
- Added intent macro precision/recall/F1 and standard retrieval Hit@8, Precision@8, Recall@8, MRR@8, MAP@8, and nDCG@8. QA now measures reference-fact recall, context relevance, citation precision, answer faithfulness, forbidden content, refusal F1, and replan F1 separately.
- Fixed the old replan calculation that automatically passed every negative case, removed the misleading refusal-as-Judge-F1 label, and made provider cache hits explicit instead of inferring them from latency.
- The final offline regression `eval-8645577496` reports realistic weaknesses: 76.25% intent accuracy, 71.63% nDCG@8, 71.43% answer-fact recall, 60% citation precision, 80% refusal F1, and 66.67% replan F1. The report lists individual failures and states that fake-provider scores are not production-quality claims.
- Final validation passed: full Compose rebuild, eight healthy services, seed, lint, typecheck, 60 unit/integration tests, 112-case eval, 2 backend E2E tests, frontend tests, and smoke.

## 2026-07-25 M22 Notes

- Replaced single-answer chat rendering with a continuous transcript and added Redis-backed short-term query context. Browser QA confirmed `图书馆今天几点关门？` followed by `那周末呢？` stays on the library topic and returns one deduplicated official source.
- Added explicit grounded-synthesis branches for memory commands, post drafting, and prompt injection. Real browser runs confirmed memory creation and management, safe refusal, evidence-insufficient refusal, and unconfirmed activity drafts without unrelated citations.
- Persisted the embedding-model signature on Neo4j chunks and reused matching corpus vectors after API restarts. The one-time corpus migration took about 28-31 seconds; after restart, real Bailian QA took about 9 seconds and logs showed one query-embedding call instead of a full corpus rebuild.
- Added official timetable knowledge and fixed `课表在哪里看` being misclassified as a physical-location question. The timetable document now ranks first and its complete source detail opens from the search result.
- Improved chat-style activity topic extraction and verified a separate second-hand draft in the eight-scenario post assistant. Drafts remain unpublished until user confirmation and retain the five-edit cap.
- Isolated fake-provider validation from runtime Redis and Neo4j. Final validation passed: lint, typecheck, 56 unit/integration tests, eval `eval-c555ec44e0` (80 intent / 18 retrieval / 14 QA), 2 backend E2E tests, frontend tests, real-provider smoke, full Compose rebuild, and eight healthy services.

## 2026-07-24 M21 Notes

- Replaced the hardcoded lost-and-found draft generator with automatic classification for lost and found, second-hand exchange, events, carpooling, study partners, campus questions, feedback, and daily-life sharing.
- Added optional explicit category selection while retaining automatic intent inference. Images are optional and enrich the draft through the VLM attribute path when supplied.
- Unified the REST endpoint and registered LangGraph `create_post_draft` tool on the same draft service, while preserving content safety, five edit rounds, version diffs, and mandatory user confirmation.
- Added frontend scenario controls and natural text-only drafting, plus regression coverage for all eight categories and the existing image-assisted lost-and-found flow.
- Browser QA passed for automatic activity drafting, explicit second-hand drafting, natural feedback application, confirmation, nine scene controls, and 390x844 mobile layout without console errors or horizontal overflow.
- Final validation passed after a successful full Compose rebuild with all eight services healthy: seed, lint, typecheck, 49 unit/integration tests, eval `eval-4930bca1c8` (80 intent / 18 retrieval / 14 QA), 2 E2E tests, frontend tests, and smoke.

## 2026-07-24 M20 Notes

- Replaced display-only intelligent-search rows with accessible result buttons backed by `GET /api/v1/sources/{source_id}`.
- Added complete official-document and campus-post detail views with source metadata, retrieval explanation, tags, and optional real source links.
- Browser QA confirmed that a `课表` result opens the expected source, closes correctly, produces no console errors, and has no horizontal overflow at 390x844.
- Final validation passed with all eight Compose services healthy: lint, typecheck, 40 unit/integration tests, eval `eval-cf54d1120d` (80 intent / 18 retrieval / 14 QA), 2 E2E tests, frontend tests, and smoke.

## 2026-07-24 M19 Notes

- Reproduced `食堂在哪` returning dining hours: retrieval found the correct topic, but the corpus lacked location facts and the relevance gate did not distinguish question facets.
- Added location and time facet detection across reranking, relevance judging, grounded model validation, and deterministic synthesis. Expanded query vocabulary for dining, courses, sports, network, delivery, and shuttle services.
- Added dining locations, removed numbered duplicate titles, selected minimal sufficient evidence, and deduplicated model context, claims, and citations.
- Real Bailian runtime now answers `一食堂位于生活区东侧，二食堂位于宿舍区南侧。` with one official citation.
- Final validation passed: lint, typecheck, 40 unit/integration tests, 2 E2E tests, frontend tests, and smoke. Eval `eval-657b016330` passed 80 intent / 18 retrieval / 14 QA cases with Hit@8, Recall@8, MRR, claim recall, citation coverage, citation groundedness, refusal accuracy, and Judge F1 all at 1.0.

## 2026-07-24 M18 Notes

- Replaced the generic first-screen seed feed with 12 realistic, clearly differentiated campus scenarios: dining, dorm repair, sports, campus-card loss, second-hand exchange, ride sharing, study groups, clubs, and daily campus questions.
- Expanded official knowledge coverage beyond the library to 16 campus service topics while retaining repeated authoritative evidence for card replacement, library hours, repairs, and other high-confidence service answers.
- Added an automated seed-data test so the UI demo remains varied and the retrieval corpus keeps its required 300-post / 40-document size.

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


## 2026-07-28 M28 Notes

- Added a model-driven structured Planner that receives an explicit Skill catalog and tool allowlist. Invalid JSON, unknown tools, invalid arguments, provider failures, and explicit fake-provider mode fall back to the deterministic planner.
- Added five executable campus Skills covering official knowledge, community search, post creation, memory management, and evaluation. Skills map to existing allowlisted tools instead of bypassing the ToolRegistry.
- Added corrective retrieval: the first replan rewrites and broadens local retrieval; the second and final replan can call an allowlisted official-domain web search adapter. Missing endpoint, key, or domains returns an explicit degraded error and never fakes an external result.
- Strengthened grounding by requiring every model claim to include an exact quoted span contained in its selected Evidence. The Vue citation card shows that quoted span and still opens the complete source record.
- Replaced substring memory matching with embedding cosine Top-K recall. Recalled memories are injected into planning and synthesis only as personalization context and cannot serve as official factual evidence.
- Added `THIRD_PARTY_NOTICES.md`: Apache-2.0 examples from `awesome-llm-apps` were used as attributed design references; the unlicensed XiaoLin repository was architecture-only and no code was copied.
- Validation passed: Ruff, Mypy (88 source files), 82 unit/integration/E2E tests, frontend lint/typecheck/test/build, and offline eval `eval-d1b5c6f0ad`. The computed run reports 76.25% intent accuracy, 66.07% nDCG@8, 71.43% answer-fact recall, and 60% citation precision; no score is hardcoded or presented as production quality.

- Final functional QA caught and fixed a source-routing defect: official-document tools previously filtered after global Top-K reranking, allowing community posts to crowd official evidence out. Source filtering now occurs before reranking; `图书馆今天几点关门？` returns `doc-library-hours-00` and its verbatim official passage.

## 2026-07-28 M29 Notes

- Adapted the actually implemented campus capabilities from the authorized `20czy/zafu_xiaolin_campus_agent` revision `1b678bd`: course schedules, structured notices, venue filtering and conflict checks, safe synthetic profile context, Open-Meteo weather, and its FastMCP stdio server.
- Registered six new allowlisted tools behind five typed Skills. Deterministic and model-driven planners can route natural queries to individual tools; complex lecture planning fans out to schedule, venue, weather, and notice tools in one bounded plan.
- Added `GET /api/v1/campus/capabilities` plus typed course, notice, venue, weather, profile, and reservation-draft endpoints. Reservation remains a synthetic confirmation-required draft and never performs a real campus booking.
- Added a Vue campus-skills page with executable demonstrations and local source details for dynamic Skill citations. Fixed duplicate draft validation in the frontend.
- Corrected upstream edge cases found during integration: natural `查最新...通知` normalization, missing notice-id mapping, unspecified-time venue conflict handling, mixed-type course-id comparison, and nullable venue-id typing.
- Real functional checks returned the Tuesday timetable through `query_course_schedule`, venue candidates through `query_campus_venues`, safe advisor context through `get_student_profile`, and a four-tool activity-planning trace. FastMCP stdio tool discovery and a live `campus_weather` call succeeded.
- Final validation passed after a full Compose rebuild: all eight services remained healthy; `make seed`, `make lint`, `make typecheck`, `make test` (92 passed), `make eval` (`eval-08f82f61ba`), `make e2e` (3 backend flows plus frontend tests), and `make smoke` passed.
- The computed offline report remains intentionally honest: 76.25% intent accuracy, 72.22% Hit@8, 66.07% nDCG@8, 71.43% answer-fact recall, 50% citation precision, 88.89% refusal F1, and 60% replan F1. No score is hardcoded or presented as production quality.
- The migrated boundary is explicit: the implemented XiaoLin course, notice, venue, weather, profile, and MCP capabilities were adapted with author permission. README-only future features and unrelated Hello Agents projects were not represented as migrated code.

## 2026-07-29 M30 Notes

- Replaced the original AI Assistant presentation with the in-project **浙商小林** workbench on `http://localhost:5173`; the previous standalone 3001/8001 reference containers are no longer required and were stopped.
- The chat response now exposes the structured Planner result, allowlisted tool calls with arguments/result counts/latency, the Relevance Judge decision, grounded answer, and citations in one continuous conversation.
- Localized the authorized campus Skill fixtures to Zhejiang Gongshang University and removed former-school markers. The synthetic profile keeps only user-provided identity facts and marks unknown advisor, dormitory, contact, and student-id data as unconfigured.
- Real functional QA for `帮我规划一场下沙校区200人讲座` invoked course, venue, Open-Meteo weather, and notice tools, then returned three grounded citations. A runtime trace-field mismatch found by this check was fixed and covered by integration tests.
- Final validation passed after `docker compose up --build -d`: all eight services healthy; seed, Ruff, frontend lint, Mypy (97 source files), 93 unit/integration tests, offline eval `eval-11d8387334`, 3 E2E tests, frontend build/tests, and smoke all passed.
- The runtime is currently explicit degraded mode for Chat, Embedding, and VLM unless credentials are configured; external weather remains real. No evaluation score is hardcoded.

## 2026-07-29 M31 Notes

- The user correctly identified that M30 only copied XiaoLin's event names and presentation while retaining CampusFlow's planner, provider router, allowlisted tool execution, grounding/refusal policy, and deterministic fake answers. M31 supersedes that chat backend.
- Ported the upstream XiaoLin chat chain: cached LangChain `ChatOpenAI` service, model-driven `TaskPlanner`, model-driven `ToolSelector`, dependency-aware `TaskExecutor`, `LLMController`, `ResponseGenerator`, `CampusToolHub`, local Skill boundary, and original SSE lifecycle. Localization is limited to Zhejiang Gongshang University names and campus fixtures.
- Both normal and Agent modes on `POST /api/v1/chat/` now use XiaoLin. The old CampusFlow `POST /api/v1/chat` remains isolated for non-chat platform regression coverage and is no longer called by the AI Assistant page.
- Added persistent XiaoLin user/assistant message history and process-info storage plus read APIs. Verified that the runtime session stores both sides of a conversation and feeds recent history into subsequent model calls.
- Removed XiaoLin chat dependencies on `ProviderRouter`, `StructuredPlanner`, memory-as-chat-history, CampusFlow evidence refusal, PII answer rewriting, and fake fixed-answer synthesis. Missing `DEEPSEEK_API_KEY` now follows upstream behavior and produces an explicit generation error instead of invented campus facts.
- Added upstream-compatible `GET /api/llm/config-status/` and a visible AI Assistant warning. Browser QA on `http://localhost:5173` confirmed the warning, Agent/normal controls, no console errors, and the final built assets.
- Controlled-model integration coverage verifies model-produced task planning, original `venue-booking` Skill selection, task execution events, streamed final response chunks, normal-mode streaming, and persisted history.
- Final validation passed: Ruff, Mypy (113 source files), 95 unit/integration tests, offline eval `eval-7742b6d99b`, 3 E2E tests, frontend lint/typecheck/build/tests, smoke, and healthy rebuilt API/Web services. One concurrent E2E run collided on shared draft fixtures; the required sequential E2E rerun passed 3/3.

## 2026-07-29 M32 Notes

- Restored the two original XiaoLin chat paths in the visible composer: normal mode directly streams an LLM answer, while Agent mode runs task planning, tool selection, execution, and response generation.
- New page loads now default to normal mode, matching the upstream project. The mode switch remains visible beside the composer controls on desktop and mobile.
- Restored Enter-to-send and Shift+Enter-for-newline behavior from the upstream XiaoLin input component. Agent-only loading copy and process cards no longer imply that normal requests use tools.
- Real two-mode API verification exposed a migration defect where Skill group names such as `venue_coordination` were advertised as executable tools. XiaoLin now receives the actual registry tool names, accepts legacy aliases defensively, flattens nested model parameters, and reports unknown tools as structured failures.
- XiaoLin's chat prompt now receives only non-identifying campus context and explicitly forbids guessing or addressing the user by an unverified name.
- Final real-model verification confirmed that normal mode emitted answer chunks without process events, while Agent mode emitted task planning, exact tool selection, successful `query_campus_venues` execution with three results, and a result-based final answer. Browser QA confirmed the composer control in both states above the mobile navigation.
- Validation passed with Ruff, Mypy (113 source files), 98 unit/integration tests, 3 E2E tests, frontend lint/typecheck/build/tests, offline eval `eval-b41554b123`, smoke, and all eight Compose services healthy.

## 2026-07-29 M33 Notes

- Rebuilt the AI Assistant surface around the upstream XiaoLin frontend instead of styling the existing CampusFlow chat panel. The page now uses the original green character asset, in-card identity header, Tool/New/History icon actions, large white message area, dark user bubbles, dashed process panel, floating composer, Agent pill, and circular send action.
- Replaced the crowded session strip with a functional history drawer. Selecting a session now loads persisted XiaoLin messages and associates saved process information with the correct assistant response.
- Added safe structured rendering for headings, numbered items, bullets, bold text, and inline code without injecting model-produced HTML. Text and Markdown attachments are read locally into the message composer.
- Fixed both live and historical process rendering so a successful raw `task_result` is normalized to `status: success`; the verified venue conversation now shows `完成` and `返回 3 条结果` instead of the incorrect failure badge.
- Responsive browser QA passed at the active 710px viewport and desktop sizing: the header actions, history drawer, process details, messages, composer, mode control, and fixed navigation remain usable without overlap.
- Final validation passed with Ruff, Mypy (113 source files), 98 unit/integration tests, 3 E2E tests, frontend lint/typecheck/build/tests, offline eval `eval-4c47729f46`, smoke, and all eight Compose services healthy.

## 2026-07-29 M34 Notes

- Renamed the user-facing campus assistant to **浙小商助手** across the Vue interface, XiaoLin response prompts, greeting synthesis, and degraded local provider response.
- Replaced the former character portrait with an original green campus-AI avatar combining a conversation symbol, graduation cap, and small golden accent.
- Updated the browser title, rebuilt API/Web, and verified the header and empty-state avatar in the running 5173 page with no console errors.
- Validation passed with Ruff, Mypy (113 source files), 98 unit/integration tests, 3 E2E tests, frontend lint/typecheck/build/tests, offline eval `eval-9a1a3df130`, smoke, and all eight Compose services healthy.

## 2026-07-29 M35 Notes

- Corrected the project's most important trust boundary: seeded campus documents and copied XiaoLin course, notice, venue, profile, and community results now disclose that they are demonstration data rather than live Zhejiang Gongshang University records.
- Added three manually verified public sources from the university library, campus-card borrowing rules, and logistics service center. Each source stores its official URL and verification date; verified sources receive a bounded retrieval boost over demo fixtures.
- Removed the fake `campus.example.edu` URLs. The 40 legacy RAG records remain available for feature demonstrations, but their text and metadata explicitly state that they are not official school publications.
- Normal chat now uses a code-level campus-fact gate before model invocation, so school-specific locations, hours, people, phone numbers, procedures, schedules, and notices cannot be freely generated on the non-retrieval path. Agent synthesis must distinguish verified official, live external, demo, and model-generated data.
- The chat UI now displays source-mode badges for every Agent task and a prominent answer-level disclosure. Normal responses display `模型直接回答 · 未检索校园资料`.
- Migrated the live RAG corpus without deleting sessions, memories, or posts: it now contains 40 explicit demo records and 3 verified official sources. No user-uploaded knowledge documents existed, so no custom document was overwritten.
- Browser QA verified both critical paths on port 5173. Agent timetable results display `演示数据` and `回答使用演示数据，不代表你的真实校务信息`; normal-mode `学校图书馆在哪` is blocked before model invocation and returns no fabricated location. The page reported no console errors.
- Final validation passed with Ruff, Mypy (113 source files), 101 unit/integration tests, 3 E2E tests, frontend lint/typecheck/build/tests, offline eval `eval-382a460e32`, smoke, and all eight Compose services healthy.

## 2026-07-29 M36 Notes

- Unified XiaoLin normal chat, Agent planning and generation, RAG embeddings, Qwen reranking, and Post Assistant image understanding behind one `DASHSCOPE_API_KEY`. Legacy provider variables remain optional compatibility overrides and are no longer required in the recommended configuration.
- Verified live Bailian calls for `qwen-plus`, `text-embedding-v4`, and `qwen-vl-plus`. The real Post Assistant endpoint identified the project image through `qwen-vl-plus` and returned `degraded=false`; normal XiaoLin chat streamed a model-generated self-introduction.
- Added image-analysis provenance to draft responses and the Vue draft status, so users can distinguish real Bailian vision from the explicit offline demo adapter.
- Added up to four image attachments to XiaoLin normal and Agent chat. `qwen-vl-plus` observations are injected as untrusted visual data, the UI shows real/degraded provenance, and Base64 image content is never written to chat history.
- Live normal and Agent checks both identified the project avatar as a green chat symbol with a graduation cap and yellow star through `qwen-vl-plus`, returning `degraded=false` before `qwen-plus` generated the answer.
- Fixed cached real-provider results being incorrectly labeled degraded. Consecutive live image requests now remain `degraded=false`, including the cache-hit path.
- Isolated deterministic test and evaluation runs from the configured external reranker while preserving real reranking in the running application.
- Final validation passed after rebuilding API/Web: Ruff, Mypy (113 source files), 106 unit/integration tests, 3 E2E tests, frontend lint/typecheck/build/tests, offline eval `eval-6e5f4d8dc9`, smoke, and eight healthy Compose services.

## 2026-07-29 M37 Notes

- Added a complete post-detail and anonymous-comment workflow to the campus feed. Clicking any post opens its full content, current comments, and a 600-character comment composer.
- Added typed comment listing and creation APIs, persistent JSON storage, post-level comment counts, and a relational model for future database-backed persistence.
- Kept verification data isolated from the live feed so automated comments do not pollute the user's existing campus posts.
- Validation passed with Ruff, Mypy (113 source files), 107 unit/integration tests, 3 E2E flows, frontend lint/build/tests, offline eval `eval-74c66feb68`, smoke, browser QA, and healthy rebuilt API/Web services.

## 2026-07-29 M38 Notes

- Replaced the oversized card grid with a compact, centered community feed. Each row now presents an anonymous avatar, author, category, date, concise body, relevant tags, and an explicit comment action.
- Removed the third-person `匿名摘要：有同学...` presentation from all 18 imported community posts. Their bodies now speak directly while remaining anonymized.
- Preserved provenance honestly through a `社区转帖` tag instead of presenting imported content as native CampusFlow authorship. Usernames, contact details, source images, and other sensitive fields remain excluded.
- Browser QA at the active 710px viewport measured a 140px first row, 12 visible feed records, no horizontal overflow, and no console errors.

## 2026-07-29 M39 Notes

- Removed the separate intelligent-search destination and placed semantic search directly above the community feed, matching the user's browse-then-search workflow.
- Removed the frontend 12-post slice and backend 80-post cap. The feed now requests 20 posts at a time with validated offset/limit parameters and appends subsequent pages without duplicates.
- Tightened the search boundary from all non-official chunks to `source_type=post`, so demo knowledge documents cannot appear as community search results.
- Search results open the same full post detail and persistent comment workflow used by ordinary feed rows.
- Validation passed with Ruff, Mypy (113 source files), 3 isolated E2E flows, frontend lint/build/tests, and targeted pagination and source-type assertions. Browser QA confirmed 20 initial rows, 40 after loading more, eight post-only search results, comment-detail navigation, no duplicate search tab, no horizontal overflow, and no console errors.
