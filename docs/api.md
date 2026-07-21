# API

Use `http://localhost:8000/docs` for the OpenAPI UI after starting Docker Compose.

Important endpoints:

- `POST /api/v1/chat` returns answer, citations, degraded-mode labels, and trace.
- `GET /api/v1/chat/{session_id}/events` streams SSE events.
- `POST /api/v1/posts/search` runs image-enhanced Hybrid RAG.
- `POST /api/v1/posts/draft` creates a HITL draft.
- `POST /api/v1/posts/draft/{draft_id}/feedback` edits, confirms, or publishes after confirmation.
- `GET /api/v1/memories` consumes memory events and lists user memories.
- `DELETE /api/v1/memories/{memory_id}` deletes user memory.
- `POST /api/v1/evals/run` runs evals.
- `GET /metrics` exposes Prometheus metrics.

