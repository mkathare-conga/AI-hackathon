# run.ps1 — Project runner for Windows
# Usage: .\run.ps1 <command>

param(
    [Parameter(Position=0)]
    [ValidateSet("up","down","restart","infra","api","frontend","seed","migrate","test","logs","status","dashboard","clean","help")]
    [string]$Command = "help"
)

switch ($Command) {

    # ─── Full Stack ─────────────────────────────────────────────────────
    "up" {
        Write-Host "Starting all services..." -ForegroundColor Green
        docker compose up --build -d
    }
    "down" {
        Write-Host "Stopping all services..." -ForegroundColor Yellow
        docker compose down
    }
    "restart" {
        Write-Host "Restarting all services..." -ForegroundColor Yellow
        docker compose down
        docker compose up --build -d
    }

    # ─── Infrastructure ─────────────────────────────────────────────────
    "infra" {
        Write-Host "Starting PostgreSQL + MinIO..." -ForegroundColor Green
        docker compose up postgres minio minio-create-bucket -d
    }

    # ─── API (local dev) ────────────────────────────────────────────────
    "api" {
        Write-Host "Starting API on http://localhost:8000 ..." -ForegroundColor Green
        $env:DATA_SOURCE = "postgres"
        $env:DATABASE_URL = "postgresql://revenue_leakage:revenue_leakage@localhost:5432/revenue_leakage"
        $env:OBJECT_STORE_ENDPOINT = "http://localhost:9000"
        $env:OBJECT_STORE_ACCESS_KEY = "minioadmin"
        $env:OBJECT_STORE_SECRET_KEY = "minioadmin"
        $env:OBJECT_STORE_BUCKET = "contract-documents"
        $env:OBJECT_STORE_SECURE = "false"
        $env:AI_PROVIDER = "disabled"
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    }

    # ─── Frontend (local dev) ───────────────────────────────────────────
    "frontend" {
        Write-Host "Starting frontend on http://localhost:5173 ..." -ForegroundColor Green
        Push-Location frontend
        npm install
        npm run dev
        Pop-Location
    }

    # ─── Database ───────────────────────────────────────────────────────
    "seed" {
        Write-Host "Seeding database..." -ForegroundColor Cyan
        docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -f /docker-entrypoint-initdb.d/001_schema.sql
        docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -f /docker-entrypoint-initdb.d/002_seed.sql
    }
    "migrate" {
        Write-Host "Applying migrations..." -ForegroundColor Cyan
        docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -c "ALTER TABLE contract_documents ADD COLUMN IF NOT EXISTS extracted_text TEXT;"
        docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -c "ALTER TABLE contract_documents ADD COLUMN IF NOT EXISTS commercial_excerpt TEXT;"
        docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -c "CREATE INDEX IF NOT EXISTS idx_obligation_extractions_contract_id ON obligation_extractions(contract_id);"
        docker exec revenue-leakage-postgres psql -U revenue_leakage -d revenue_leakage -c "CREATE INDEX IF NOT EXISTS idx_obligation_extractions_document_id ON obligation_extractions(document_id);"
        Write-Host "Done." -ForegroundColor Green
    }

    # ─── Testing ────────────────────────────────────────────────────────
    "test" {
        Write-Host "Running all tests..." -ForegroundColor Cyan
        python -m pytest tests/ -v
    }

    # ─── Monitoring ─────────────────────────────────────────────────────
    "logs" {
        docker compose logs -f
    }
    "status" {
        docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    }
    "dashboard" {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/dashboard/summary"
        $response | ConvertTo-Json -Depth 5
    }

    # ─── Cleanup ────────────────────────────────────────────────────────
    "clean" {
        Write-Host "Stopping containers and removing volumes..." -ForegroundColor Red
        docker compose down -v
    }

    # ─── Help ───────────────────────────────────────────────────────────
    "help" {
        Write-Host ""
        Write-Host "Usage: .\run.ps1 <command>" -ForegroundColor White
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Cyan
        Write-Host "  up         Start all services (Docker Compose)"
        Write-Host "  down       Stop all services"
        Write-Host "  restart    Rebuild and restart everything"
        Write-Host "  infra      Start PostgreSQL + MinIO only"
        Write-Host "  api        Run API locally (hot-reload, needs infra)"
        Write-Host "  frontend   Run React frontend locally"
        Write-Host "  seed       Re-seed the database"
        Write-Host "  migrate    Apply schema migrations"
        Write-Host "  test       Run all tests"
        Write-Host "  logs       Tail container logs"
        Write-Host "  status     Show container status"
        Write-Host "  dashboard  Fetch dashboard summary"
        Write-Host "  clean      Stop + delete volumes (fresh start)"
        Write-Host ""
    }
}
