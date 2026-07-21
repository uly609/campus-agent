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

## Degraded Mode Policy

External model credentials are optional for local demo and test runs. When absent, chat, embedding, and VLM providers use explicit fake adapters and include degraded-mode traces. PostgreSQL, Redis, and Neo4j are represented as real Docker Compose services for the full demo.
