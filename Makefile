.PHONY: all up down infra api frontend seed migrate logs status clean help

# ─── Full Stack ────────────────────────────────────────────────────────────────

all: up ## Start everything with Docker Compose

up: ## Start all services (build if needed)
	docker compose up --build -d

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose down
	docker compose up --build -d

# ─── Infrastructure Only ──────────────────────────────────────────────────────

infra: ## Start PostgreSQL + MinIO only
	docker compose up postgres minio minio-create-bucket -d

# ─── Individual Components (local dev, no Docker for app) ─────────────────────

api: ## Run FastAPI backend locally (requires infra running)
	@echo "Starting API on http://localhost:8000 ..."
	set DATA_SOURCE=postgres&& \
	set DATABASE_URL=postgresql://revenue_leakage:revenue_leakage@localhost:5432/revenue_leakage&& \
	set OBJECT_STORE_ENDPOINT=http://localhost:9000&& \
	set OBJECT_STORE_ACCESS_KEY=minioadmin&& \
	set OBJECT_STORE_SECRET_KEY=minioadmin&& \
	set OBJECT_STORE_BUCKET=contract-documents&& \
	set OBJECT_STORE_SECURE=false&& \
	set AI_PROVIDER=disabled&& \
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend: ## Run React frontend locally
	cd frontend && npm install && npm run dev

# ─── Database ─────────────────────────────────────────────────────────────────

seed: ## Seed the database (runs init scripts)
	docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -f /docker-entrypoint-initdb.d/001_schema.sql
	docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -f /docker-entrypoint-initdb.d/002_seed.sql

migrate: ## Apply schema migrations to running DB
	docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -c "ALTER TABLE contract_documents ADD COLUMN IF NOT EXISTS extracted_text TEXT;"
	docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -c "ALTER TABLE contract_documents ADD COLUMN IF NOT EXISTS commercial_excerpt TEXT;"
	docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -c "CREATE INDEX IF NOT EXISTS idx_obligation_extractions_contract_id ON obligation_extractions(contract_id);"
	docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -c "CREATE INDEX IF NOT EXISTS idx_obligation_extractions_document_id ON obligation_extractions(document_id);"

# ─── Testing ──────────────────────────────────────────────────────────────────

test: ## Run all tests
	python -m pytest tests/ -v

test-leakage: ## Run leakage detection tests only
	python -m pytest tests/test_leakage.py -v

test-ingestion: ## Run document ingestion tests only
	python -m pytest tests/test_document_ingestion.py -v

# ─── Monitoring ───────────────────────────────────────────────────────────────

logs: ## Tail logs from all containers
	docker compose logs -f

logs-api: ## Tail API container logs
	docker logs -f revenue-leakage-api

status: ## Show container status
	docker compose ps

health: ## Check API health endpoint
	curl -s http://localhost:8000/healthz || echo "API not responding"

dashboard: ## Fetch dashboard summary from API
	curl -s http://localhost:8000/api/dashboard/summary | python -m json.tool

# ─── Cleanup ──────────────────────────────────────────────────────────────────

clean: ## Stop containers and remove volumes (fresh start)
	docker compose down -v

# ─── Help ─────────────────────────────────────────────────────────────────────

help: ## Show this help
	@echo Available targets:
	@findstr /R "^[a-z][a-z-]*:.*##" Makefile
