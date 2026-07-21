SHELL := /bin/bash
PYTHON ?= python
COMPOSE ?= docker compose
API_SERVICE ?= api

.PHONY: lint typecheck test eval e2e smoke seed db-up migrate down logs frontend-check

lint:
	$(COMPOSE) run --rm --no-deps $(API_SERVICE) ruff check backend evals scripts
	cd frontend && npm run lint

typecheck:
	$(COMPOSE) run --rm --no-deps --workdir /app/backend $(API_SERVICE) mypy --explicit-package-bases app
	cd frontend && npm run typecheck

test:
	$(COMPOSE) run --rm --no-deps $(API_SERVICE) pytest backend/tests/unit backend/tests/integration

e2e:
	$(COMPOSE) run --rm $(API_SERVICE) pytest backend/tests/e2e
	cd frontend && npm run test

eval:
	$(COMPOSE) run --rm --no-deps $(API_SERVICE) python evals/run_eval.py --write-report

seed:
	$(COMPOSE) run --rm --no-deps $(API_SERVICE) python scripts/seed.py

db-up:
	$(COMPOSE) up -d postgres redis neo4j

migrate:
	$(COMPOSE) run --rm --no-deps $(API_SERVICE) python scripts/migrate.py

smoke:
	$(COMPOSE) run --rm --no-deps $(API_SERVICE) python scripts/smoke.py

frontend-check:
	cd frontend && npm run lint && npm run typecheck && npm run test

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs --tail=120 api web
