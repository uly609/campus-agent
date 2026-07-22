# CampusFlow AI

CampusFlow AI is a Python-first campus community agent demo with FastAPI, a Vue 3-style demo UI, Hybrid RAG, GraphRAG, multimodal search, human-in-the-loop post drafting, Redis Streams memory, evals, and observability.

The runtime uses a compiled LangGraph `StateGraph`. Hybrid retrieval combines Chinese-aware BM25, routed embeddings, Neo4j Vector Index queries, Neo4j GraphRAG expansion, relevance reranking, and RRF.

## Degraded Mode

The Docker demo starts PostgreSQL, Redis, Neo4j, Prometheus, Grafana, and Alertmanager as real services. Model credentials are optional. If chat, embedding, or VLM credentials are absent, CampusFlow uses explicit fake providers and returns degraded-mode trace labels such as `fake_chat_provider`, `fake_embedding_provider`, and `fake_vlm_provider`.

Student-card OCR is synthetic-demo only and rejects non-demo images.

## Real Model Providers

Each role supports `local_primary`, `local_backup`, and `cloud_fallback` through an OpenAI-compatible HTTP contract. Set the role-specific base URL and model in `.env`; local API keys may be empty when the server permits it.

```bash
cp .env.example .env
# Example local OpenAI-compatible server
LOCAL_PRIMARY_CHAT_URL=http://host.docker.internal:11434
LOCAL_PRIMARY_CHAT_MODEL=qwen2.5:7b
LOCAL_PRIMARY_EMBEDDING_URL=http://host.docker.internal:11434
LOCAL_PRIMARY_EMBEDDING_MODEL=bge-m3
LOCAL_PRIMARY_VLM_URL=http://host.docker.internal:11434
LOCAL_PRIMARY_VLM_MODEL=qwen2.5-vl:7b
```

For DashScope-compatible cloud fallback, set the relevant `CLOUD_FALLBACK_*_URL` to `https://dashscope.aliyuncs.com/compatible-mode/v1`, select the model, and provide `OPENAI_API_KEY` or `VLM_API_KEY`. Provider calls have bounded retries, timeouts, Redis exact-match caching, and explicit fake fallback traces.

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
2. Ask `图书馆今天几点关门？` in AI Assistant and inspect citations plus node trace.
3. Run smart search with `南门 捡到 校园卡`; results show BM25/vector/graph/RRF explanations.
4. Generate a post draft with synthetic image `synthetic-card-library-blue.png`, edit it up to five rounds, then confirm.
5. Ask the assistant `记住我喜欢图书馆靠窗座位`, open Memory Management, and delete the memory.
6. Run Eval Dashboard and inspect the computed metrics.
7. Open `/metrics` or Grafana for request, LLM, tool, replan, cache, citation, and retrieval metrics.

## Main API

- `POST /api/v1/chat`
- `GET /api/v1/chat/{session_id}/events`
- `POST /api/v1/posts/search`
- `POST /api/v1/posts/draft`
- `POST /api/v1/posts/draft/{draft_id}/feedback`
- `GET /api/v1/memories`
- `DELETE /api/v1/memories/{memory_id}`
- `POST /api/v1/evals/run`
- `GET /metrics`

## Data

`make seed` creates 300 Chinese campus posts and 30 official campus documents under `data/generated`. Eval datasets are generated as human-readable JSONL files under `evals/datasets` if missing, then reports are written to `evals/reports`.
