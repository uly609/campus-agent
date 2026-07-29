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

## M15 - Real Provider Runtime Validation

- [x] Configure Bailian Chat, Embedding, and VLM cloud-fallback roles without committing credentials.
- [x] Validate each role with a real OpenAI-compatible API call.
- [x] Batch corpus embeddings and reuse the retrieval index for practical real-provider startup latency.
- [x] Force fake adapters for deterministic tests and evals while retaining real-provider smoke coverage.
- [x] Run lint, typecheck, tests, eval, E2E, frontend tests, and real-provider smoke with healthy Compose services.

## M16 - Vue UI Runtime Hardening

- [x] Replace static HTML string rendering with a real Vue 3 + Vite application.
- [x] Remove raw JSON and provider debug fields from user-facing views.
- [x] Add real image upload, preview, VLM drafting, editing, and confirmation.
- [x] Normalize multilingual and scalar/list VLM attributes at the API boundary.
- [x] Render readable chat citations, retrieval explanations, eval metrics, memories, and traces.
- [x] Verify core flows in a real browser at desktop and mobile viewports with no console errors.
- [x] Run full validation with all eight Compose services healthy.

## M17 - Product Platform Hardening

- [x] Add managed knowledge documents with lifecycle status and content-hash deduplication.
- [x] Add Redis Streams ingestion jobs with progress, bounded retry, and failure visibility.
- [x] Add runtime provider profiles with encrypted credentials and connectivity checks.
- [x] Add Redis-backed API rate limiting and user-visible session management.
- [x] Add Vue knowledge-base, provider, task, and session management surfaces.
- [x] Validate platform flows, update architecture docs, and run all stop-condition commands.

## M18 - Campus Demo Data Curation

- [x] Add a curated, first-screen campus-week feed covering dining, dorms, sports, lost and found, ride sharing, study, clubs, and second-hand exchange.
- [x] Expand official knowledge to course selection, exams, campus card, dining, sports venues, delivery, counseling, network, shuttle, internship, clubs, and graduation.
- [x] Preserve 300 posts, 40 official documents, and strong authoritative retrieval coverage for campus-service answers.
- [x] Add seed-data coverage tests and run the full validation suite.

## M19 - Query-Facet RAG Precision

- [x] Reproduce the location-question failure from runtime traces and real-provider calls.
- [x] Expand campus queries for dining, courses, sports, network, delivery, and shuttle services.
- [x] Add location/time query-facet matching to post-fusion reranking and the Relevance Judge.
- [x] Require grounded model claims to answer the requested facet.
- [x] Use minimal sufficient evidence and deduplicate excerpts, claims, and citations.
- [x] Add regression tests for `食堂在哪` and run the full validation suite.

## M20 - Search Source Detail Experience

- [x] Add a typed source-detail API for official knowledge and campus posts.
- [x] Make every intelligent-search result keyboard-accessible and clickable.
- [x] Show full source content, provenance, metadata, tags, and retrieval explanation.
- [x] Hide synthetic demo URLs instead of presenting them as external links.
- [x] Add responsive detail-dialog behavior and Escape/close controls.
- [x] Validate desktop and mobile interactions in a real browser.

## M21 - Multi-Scenario Campus Post Agent

- [x] Replace the lost-and-found-only draft template with eight campus post scenarios.
- [x] Add automatic intent classification and optional explicit category selection.
- [x] Support text-only drafting with optional VLM image enhancement.
- [x] Reuse the same draft service from the LangGraph tool registry and REST API.
- [x] Preserve content safety, five edit rounds, and human confirmation before publishing.
- [x] Add scenario coverage, E2E coverage, frontend controls, and browser QA.

## M22 - Functional Conversation Acceptance

- [x] Preserve short-term session context and resolve natural follow-ups such as `那周末呢？`.
- [x] Render a continuous user/assistant transcript and deduplicate displayed sources.
- [x] Route memory, post drafting, and prompt-injection requests to explicit non-RAG responses.
- [x] Persist and reuse Neo4j corpus embeddings across API restarts.
- [x] Separate fake-provider tests from runtime Redis and Neo4j data.
- [x] Add timetable knowledge and distinguish lookup questions from physical-location questions.
- [x] Improve chat-style activity drafting and retain eight standalone post scenarios.
- [x] Validate real Bailian conversations, memory, drafting, search detail, refusal, and security behavior in the browser.
- [x] Run the complete validation suite with all eight Compose services healthy.

## M23 - Honest Evaluation V2

- [x] Replace source-prefix relevance with exact human-authored graded qrels.
- [x] Add paraphrase, overlapping-intent, implicit, hard-negative, partial-evidence, conflict, OOD, and prompt-injection cases.
- [x] Add standard intent macro metrics and retrieval Hit, Precision, Recall, MRR, MAP, and nDCG metrics.
- [x] Separate answer facts, context relevance, citation precision, faithfulness, refusal F1, and replan F1.
- [x] Fix non-replan cases being counted as automatic successes and stop labeling refusal F1 as Judge F1.
- [x] Record explicit cache-hit state instead of inferring it from zero latency.
- [x] Show failed cases and offline fake-provider limitations in JSON, Markdown, and Vue reports.
- [x] Run the complete validation suite with all eight Compose services healthy.

## M24 - Community Retrieval And Complete Publishing

- [x] Replace the custom BM25 scorer with the maintained `rank-bm25` implementation.
- [x] Rerank RRF-fused candidates with Bailian `qwen3-rerank` when configured.
- [x] Keep an explicit lexical fallback when the external reranker is unavailable.
- [x] Reject same-topic passages that do not answer the requested location or time facet.
- [x] Add a real confirm-then-publish action to the Vue post assistant.
- [x] Make draft publishing idempotent and block publication before confirmation.
- [x] Validate real browser publishing, insufficient-evidence refusal, all tests, evals, E2E, smoke, and eight healthy services.

## M25 - Published Post Memory Integration

- [x] Carry the active user and session through post drafting and publication.
- [x] Publish first-person facts and preferences from confirmed posts to Redis Streams.
- [x] Recognize residence statements such as `我住在` without memorizing generic location posts.
- [x] Create at most one memory event for repeated publication requests.
- [x] Backfill the affected demo post and validate lint, typecheck, tests, eval, E2E, and smoke.

## M26 - Typed Intent Planning

- [x] Add Pydantic v2 `IntentPlan` and `ToolCall` boundary schemas.
- [x] Add `StructuredPlanner` while retaining the deterministic fallback planner.
- [x] Validate planned tools and required arguments against the active `ToolRegistry` before execution.
- [x] Keep the existing 13-node LangGraph workflow and legacy planner adapter compatible.
- [x] Add planner schema, tool allowlist, argument validation, and graph regression tests.
- [x] Add citation provenance validation, corrective retrieval trace metrics, memory recall metrics, and Vue citation/trace interaction improvements.

## M27 - Eval And Final Regression Hardening

- [x] Validate intent accuracy, planner/tool contract metrics, citation precision, faithfulness, and corrective RAG metrics.
- [x] Validate memory recall evaluation coverage and conflict/supersedes behavior.
- [x] Run offline deterministic eval reports and keep provider limitations explicit.
- [x] Complete final full validation, documentation sync, and release commit.


## M28 - Dynamic Skills And Corrective Retrieval

- [x] Model-driven typed Planner with deterministic degraded fallback.
- [x] Skill catalog mapped to the allowlisted ToolRegistry.
- [x] Query rewrite and bounded official-domain web fallback.
- [x] Verbatim claim-evidence citation spans.
- [x] Embedding Top-K long-term-memory recall for personalization only.
- [x] Reference-project license and attribution notice.
- [x] Frontend citation quote rendering.
- [x] Ruff, Mypy, unit, integration, E2E, eval, frontend, Compose, and smoke validation.

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

## M29 - Authorized XiaoLin Campus Skill Integration

- [x] Adapt authorized course-schedule, campus-notice, venue, synthetic-profile, and weather services.
- [x] Register five new typed Skills and six allowlisted tools in the Planner-Executor workflow.
- [x] Add multi-tool campus activity planning with schedule, venue, weather, and notice fan-out.
- [x] Add a runnable FastMCP stdio weather server backed by Open-Meteo.
- [x] Add privacy-safe profile projection and confirmation-only venue reservation drafts.
- [x] Add campus capability APIs and a clickable Vue campus-skills demonstration page.
- [x] Add regression coverage for natural-language routing, notice filtering, venue conflicts, MCP registration, and safe profile fields.
- [x] Complete full Compose, test, eval, E2E, smoke, functional UI, documentation, commit, and push validation.

## M30 - ZJSU XiaoLin Chat Workbench

- [x] Replace the CampusFlow AI Assistant surface with the Zhejiang Gongshang XiaoLin chat workbench.
- [x] Expose validated Planner steps, tool selections, execution outcomes, and relevance decisions in each answer.
- [x] Localize campus, profile, course, venue, and weather demonstration data without inventing unknown personal fields.
- [x] Keep all calls behind the existing ToolRegistry, grounding policy, citations, and two-replan cap.
- [x] Add regression coverage for the complete planner-tool-judge trace and XiaoLin frontend surface.
- [x] Rebuild all eight services and pass seed, lint, typecheck, test, eval, E2E, and smoke validation.
