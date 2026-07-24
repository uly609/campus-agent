# API

Use `http://localhost:8000/docs` for the OpenAPI UI after starting Docker Compose.

Important endpoints:

- `POST /api/v1/chat` returns answer, citations, degraded-mode labels, and trace.
- `GET /api/v1/chat/{session_id}/events` streams SSE events.
- `GET|POST /api/v1/sessions` lists or creates conversations; `DELETE /api/v1/sessions/{id}` removes one.
- `GET|POST /api/v1/knowledge/documents` manages knowledge and starts asynchronous indexing.
- `GET /api/v1/knowledge/jobs` lists progress; `POST /api/v1/knowledge/jobs/{id}/retry` retries within the bounded attempt budget.
- `GET|POST /api/v1/providers` manages redacted model profiles; `POST /api/v1/providers/{id}/check` performs a non-generating connectivity check.
- Rate-limited responses expose `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- `POST /api/v1/posts/search` runs image-enhanced Hybrid RAG.
- `POST /api/v1/posts/draft` creates a HITL draft.
- `POST /api/v1/posts/draft/{draft_id}/feedback` edits, confirms, or publishes after confirmation.
- `GET /api/v1/memories` consumes memory events and lists user memories.
- `DELETE /api/v1/memories/{memory_id}` deletes user memory.
- `POST /api/v1/evals/run` runs evals.
- `GET /metrics` exposes Prometheus metrics.
