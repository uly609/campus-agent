# CampusFlow AI - Complete Project Specification

CampusFlow AI is an AI-driven campus anonymous community, campus knowledge QA, intelligent post retrieval, and AI-assisted post drafting platform.

The implementation focus is a Python-first multi-stage agent with Hybrid RAG, GraphRAG, multimodal understanding, long-term memory, provider fallback, evaluation, and observability. FastAPI exposes the runtime API and Vue 3 provides the demo UI.

## Required Agent Flow

The main workflow has exactly these six stages:

1. Coreference resolution.
2. Visual understanding.
3. Intent planning.
4. Tool execution.
5. Relevance gate and replan.
6. Grounded synthesis.

The explicit nodes are:

`input_guard_node`, `load_memory_node`, `coreference_resolver_node`, `visual_understanding_node`, `intent_planner_node`, `tool_executor_node`, `retrieval_gate_node`, `relevance_judge_node`, `replan_node`, `grounded_synthesis_node`, `output_guard_node`, `publish_memory_event_node`, and `persist_trace_node`.

## Retrieval

Hybrid RAG uses BM25, bge-m3-compatible 1024-dimensional embeddings, Neo4j vector retrieval, GraphRAG expansion, and reciprocal-rank fusion. Factual answers are grounded in evidence with source id, source type, title, excerpt, score, official flag, and metadata.

## Safety

CampusFlow treats retrieved documents and posts as untrusted data, detects prompt injection at input/retrieval/generation layers, refuses evidence-insufficient factual answers, binds claims to evidence, filters PII, and limits replans to two.

## Providers

Chat, embedding, and VLM roles route through local-primary, local-backup, and cloud-fallback providers. Redis SETEX exact-match cache is used for deterministic cacheable calls. Fake providers are explicit and used for tests or missing credentials.

## Multimodal And HITL

The app extracts image attributes, enhances search with image-derived filters, performs privacy-safe synthetic student-card OCR, and supports human-in-the-loop post drafting with at most five edit rounds. Drafts publish only after user confirmation.

## Memory

Long-term memory is event-driven with Redis Streams, extraction, hash and embedding deduplication, conflict detection, supersedes links, event expiry, and user deletion controls.

## API Surface

Required endpoints:

- `GET /health`
- `GET /ready`
- `POST /api/v1/chat`
- `GET /api/v1/chat/{session_id}/events`
- `POST /api/v1/posts`
- `GET /api/v1/posts`
- `GET /api/v1/posts/{post_id}`
- `POST /api/v1/posts/search`
- `POST /api/v1/posts/draft`
- `POST /api/v1/posts/draft/{draft_id}/feedback`
- `POST /api/v1/ingest/documents`
- `POST /api/v1/ingest/rebuild-index`
- `GET /api/v1/memories`
- `DELETE /api/v1/memories/{memory_id}`
- `POST /api/v1/evals/run`
- `GET /api/v1/evals/{run_id}`
- `GET /metrics`

## Frontend

Vue 3 demo pages: post feed, AI assistant with citations and traces, multimodal search, HITL post drafting, memory management, eval reports, and execution traces.

## Evaluation

Datasets include 80 intent cases, 18 retrieval cases, and 14 QA cases. Metrics are computed from actual predictions and written as JSON plus Markdown reports. Scores are never hardcoded.

## Infrastructure

Docker Compose runs api, web, postgres, redis, neo4j, prometheus, grafana, and alertmanager. Missing model credentials put only model providers into explicit degraded fake mode.

