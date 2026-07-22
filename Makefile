SHELL := /bin/bash
PYTHON ?= python
COMPOSE ?= docker compose
API_SERVICE ?= api
FAKE_PROVIDER_ENV = -e LOCAL_PRIMARY_CHAT_URL= -e LOCAL_BACKUP_CHAT_URL= -e CLOUD_FALLBACK_CHAT_URL= \
	-e LOCAL_PRIMARY_EMBEDDING_URL= -e LOCAL_BACKUP_EMBEDDING_URL= -e CLOUD_FALLBACK_EMBEDDING_URL= \
	-e LOCAL_PRIMARY_VLM_URL= -e LOCAL_BACKUP_VLM_URL= -e CLOUD_FALLBACK_VLM_URL=

.PHONY: lint typecheck test eval e2e smoke seed db-up migrate down logs frontend-check

lint:
	$(COMPOSE) run --rm --no-deps $(API_SERVICE) ruff check backend evals scripts
	cd frontend && npm run lint

typecheck:
	$(COMPOSE) run --rm --no-deps --workdir /app/backend $(API_SERVICE) mypy --explicit-package-bases app
	cd frontend && npm run typecheck

test:
	$(COMPOSE) run --rm --no-deps $(FAKE_PROVIDER_ENV) $(API_SERVICE) pytest backend/tests/unit backend/tests/integration

e2e:
	$(COMPOSE) run --rm --no-deps $(FAKE_PROVIDER_ENV) $(API_SERVICE) pytest backend/tests/e2e
	cd frontend && npm run test

eval:
	$(COMPOSE) run --rm --no-deps $(FAKE_PROVIDER_ENV) -v "$$(pwd)/evals:/app/evals" $(API_SERVICE) python -c "import runpy, sys; sys.argv=['evals/run_eval.py','--write-report']; runpy.run_path('evals/run_eval.py', run_name='__main__')"

seed:
	$(COMPOSE) run --rm --no-deps $(API_SERVICE) python scripts/seed.py

db-up:
	$(COMPOSE) up -d postgres redis neo4j

migrate:
	$(COMPOSE) run --rm --no-deps -e DATABASE_URL=sqlite:///data/generated/campusflow.db $(API_SERVICE) python scripts/migrate.py

smoke:
	$(COMPOSE) run --rm --no-deps $(API_SERVICE) python scripts/smoke.py

frontend-check:
	cd frontend && npm run lint && npm run typecheck && npm run test

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs --tail=120 api web
