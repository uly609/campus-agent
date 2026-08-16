# AtlasHub AI

AtlasHub AI is a Python-first enterprise knowledge community and governance Agent. It combines a chat-first Agent, managed knowledge ingestion, Hybrid RAG, GraphRAG, multimodal community content, explainable feed ranking, human-reviewed moderation, Redis Streams memory, evals, and observability. The current repository keeps the former campus adapters as migration-compatible fixtures while the product surface is being moved to the enterprise knowledge domain.

The runtime uses a compiled LangGraph `StateGraph`. Hybrid retrieval combines `rank-bm25`, routed embeddings, Neo4j Vector Index queries, Neo4j GraphRAG expansion, RRF, and optional Bailian `qwen3-rerank` reranking.

## Degraded Mode

The Docker demo starts PostgreSQL, Redis, Neo4j, Prometheus, Grafana, and Alertmanager as real services. Model credentials are optional. If chat, embedding, or VLM credentials are absent, CampusFlow uses explicit fake providers and returns degraded-mode trace labels such as `fake_chat_provider`, `fake_embedding_provider`, and `fake_vlm_provider`.

Student-card OCR is synthetic-demo only and rejects non-demo images.

## Real Model Providers

Each role supports `local_primary`, `local_backup`, and `cloud_fallback` through an OpenAI-compatible HTTP contract. Set the role-specific base URL and model in `.env`; local API keys may be empty when the server permits it.

```bash
cp .env.example .env
# Unified DashScope/Bailian setup for XiaoLin chat, retrieval, reranking, and post-image understanding
DASHSCOPE_API_KEY=...
DASHSCOPE_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
AGENT_MAIN_MODEL=qwen-plus
TOOL_LIBRARY_MODEL=qwen-plus
CLOUD_FALLBACK_CHAT_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
CLOUD_FALLBACK_CHAT_MODEL=qwen-plus
CLOUD_FALLBACK_EMBEDDING_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
CLOUD_FALLBACK_EMBEDDING_MODEL=text-embedding-v4
CLOUD_FALLBACK_VLM_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
CLOUD_FALLBACK_VLM_MODEL=qwen-vl-plus
```

The single `DASHSCOPE_API_KEY` powers XiaoLin chat, RAG embeddings, reranking, and `qwen-vl-plus` image analysis in both AI Assistant chat and the Post Assistant. XiaoLin accepts up to four JPEG, PNG, or WebP images. Agent mode also accepts Excel, CSV, PDF, TXT, and Markdown documents, with a 10MB per-file and 20MB aggregate limit. Only safe visual summaries and parsed document chunks enter model context; raw attachments are not persisted in chat history. `OPENAI_API_KEY`, `VLM_API_KEY`, and `RERANK_API_KEY` remain optional compatibility overrides. Provider calls have bounded retries, timeouts, Redis exact-match caching, and explicit fake fallback traces.

To enable external candidate reranking, set `RERANK_MODEL=qwen3-rerank`; the endpoint and key can be supplied through `RERANK_URL` and `RERANK_API_KEY`, or derived from the DashScope chat endpoint and `DASHSCOPE_API_KEY`. Without them, retrieval reports `reranker_not_configured` and uses its lexical fallback.

Providers can also be added from the **模型** page. Runtime keys are encrypted at rest using `CAMPUSFLOW_PROVIDER_ENCRYPTION_SECRET`, never returned to the browser, and checked through the non-generating `/models` compatibility endpoint.

## One-Command Demo

Alertmanager uses the pinned official `quay.io/prometheus/alertmanager:v0.27.0`
image with the repository configuration baked into a thin local layer. No untracked binary archive is required.

```bash
docker compose up --build -d
make seed
make smoke
```

Open:

- API: http://localhost:8000/docs
- Web UI: http://localhost:5173
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 with `admin` / `campusflow`

## Full Validation

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

## Demo Script

1. Open the web UI and refresh the post feed.
2. Open **AI 学问**, ask `帮我规划一场下沙校区200人讲座`, and inspect the XiaoLin task plan, selected Skills, execution results, relevance decision, answer, and citations.
3. Run smart search with `南门 捡到 校园卡`; results show BM25/vector/graph/RRF explanations.
4. Generate a post draft with optional synthetic image `synthetic-card-library-blue.png`, edit it up to five rounds, confirm it, click **发布帖子**, and verify it appears in the post feed.
5. Ask the assistant `记住我喜欢图书馆靠窗座位`, open Memory Management, and delete the memory.
6. Run Eval Dashboard and inspect the computed metrics.
7. Add a TXT, Markdown, Excel, CSV, PDF, or image file in Knowledge Base; non-text files are parsed into editable chunks before indexing.
8. Add or check a Chat, Embedding, or VLM route in Model Routing.
9. Open `/metrics` or Grafana for request, LLM, tool, replan, cache, citation, and retrieval metrics.
10. Enable **Agent** in AI Assistant: a greeting selects only General Worker, a campus fact selects XiaoLin Campus Worker, and a compound request selects only the required workers. `POST /api/v1/agents/multi` exposes the same graph for API inspection.
11. Like several posts, compare **最新 / 热门 / 为你推荐**, report a test post, then open **社区治理** to review it and inspect the audit trail.

Long-term memory accepts explicit chat memories and eligible first-person facts or preferences from confirmed published posts. Generic post content is not memorized. Open **记忆** after publishing to consume the Redis Stream and inspect or delete the resulting record.

## Main API

- `POST /api/v1/chat`
- `GET /api/v1/chat/{session_id}/events`
- `POST /api/v1/posts/search`
- `POST /api/v1/posts/draft`
- `POST /api/v1/posts/draft/{draft_id}/feedback`
- `POST /api/v1/posts/{post_id}/reactions`
- `POST /api/v1/posts/{post_id}/reports`
- `GET /api/v1/community/moderation/reports`
- `POST /api/v1/community/moderation/reports/{report_id}/review`
- `GET /api/v1/community/audit`
- `GET /api/v1/memories`
- `DELETE /api/v1/memories/{memory_id}`
- `GET|POST /api/v1/knowledge/documents`
- `GET /api/v1/knowledge/jobs`
- `POST /api/v1/knowledge/jobs/{job_id}/retry`
- `POST /api/v1/files/parse`
- `POST /api/v1/agents/multi`
- `GET /api/v1/agents/multi/spec`
- `GET|POST /api/v1/providers`
- `POST /api/v1/providers/{provider_id}/check`
- `GET|POST /api/v1/sessions`
- `POST /api/v1/evals/run`
- `GET /metrics`

## Data

`make seed` creates 300 Chinese demo campus posts, 40 explicitly labeled demo documents, and 3 manually verified Zhejiang Gongshang University public sources under `data/generated`. Verified records retain their official URLs and verification dates; demo records never use fake official URLs. The first screen deliberately includes a varied campus-week demo feed: dining, dorm repair, course selection, sports, campus-card loss, second-hand exchange, ride sharing, study groups, clubs, and health services. Eval datasets are generated as human-readable JSONL files under `evals/datasets` if missing, then reports are written to `evals/reports`.


## AtlasHub chat workbench

The **AI 助手** page is the primary AtlasHub Agent surface. Each Agent response shows its task plan, selected tools, execution results, and source mode. Knowledge documents and community content remain separate evidence classes, and human review is required before community content becomes a governed knowledge candidate. The former campus adapters remain available only for migration fixtures and regression coverage.

## Tool routing and procedural Skills

The Planner uses one typed allowlist of executable Tools. Tools are atomic actions such as knowledge retrieval, community search, official-source lookup, attachment analysis, draft generation, memory access, and evaluation-report lookup. They are validated before execution and return structured results with provenance.

Skills are not a second tool-routing layer. During governed document ingestion, `ProceduralSkillExtractor` turns evidence-backed SOP sections into reusable procedural knowledge assets containing a name, steps, inputs, outputs, evidence quote, tags, and confidence. A future LLM extractor can replace the deterministic fallback without changing this asset contract. This follows the separation used by MimirQ: Agent orchestration, executable tools, and reusable procedural knowledge are separate concerns.

## Document parsing and managed knowledge ingestion

`POST /api/v1/files/parse` turns a single upload into typed, chunked text without touching a database. TXT and Markdown use paragraph-aware chunks; Excel and CSV become Markdown table chunks (60 rows per chunk); PDFs become per-page text plus extracted tables; PNG, JPEG, and WebP go through the Qwen-VL chat-image analysis path and record provider/model/degraded metadata. Files over 10MB or with an unlisted extension are rejected. With `ingest=true`, parsed chunks are joined into a managed knowledge document and enqueued through the Redis Streams ingestion pipeline; oversized bodies are truncated with an explicit marker. The Vue Knowledge Base calls this endpoint for non-text uploads and shows the parsed chunks as editable text before indexing. AI Assistant sends document attachments into the same parser through Multimodal Worker; the resulting chunks are shared with Campus or General Worker for grounded document analysis.

## Multi-agent orchestration and RAGAS-style evaluation

AI Assistant Agent mode and `POST /api/v1/agents/multi` share a LangGraph supervisor-workers graph. The retrieval worker follows a bounded Plan-Worker pattern: it decomposes a compound request into at most four sub-queries, runs Hybrid RAG retrieval for those sub-queries, deduplicates evidence, and shares citations and extracted procedural skills through the state blackboard. Other workers handle community operations, multimodal parsing, drafting, evaluation, or general answering.

The supervisor computes a bounded worker set once and terminates when the selected workers finish or the turn limit is reached. The Tool Registry remains the only executable allowlist; workers produce task artifacts and do not create a parallel business-tool registry. `GET /api/v1/agents/multi/spec` exposes the shared state and termination contract, while prompt-injection flags and worker limits remain hard stops.

The offline eval report adds RAGAS-style `qa_faithfulness`, `qa_answer_relevancy`, `qa_context_precision`, and `qa_context_recall` using deterministic token-overlap approximations, documented as regression metrics rather than an LLM judge.

## Community ranking and governance

The post feed supports chronological, hot, and personalized modes. Hot ranking combines freshness, likes, comments, and report penalties; personalized ranking adds category and tag affinity learned only from the current user's explicit likes. Every non-chronological result carries a human-readable ranking reason.

Reports receive deterministic risk scores and `keep`, `review`, or `hide` suggestions, but the automated scorer cannot remove content. A moderator must explicitly keep or hide a post, and both report creation and final review are persisted in the community audit log. This keeps automated assistance separate from the final governance decision.
