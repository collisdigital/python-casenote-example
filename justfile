# NHS Case Notes Tracking API — task runner
# Uses `uv` for dependency management. Install: https://docs.astral.sh/uv/

set dotenv-load := true

# Bind to 0.0.0.0 so Codespaces / container port-forwarding works.
host := "0.0.0.0"
port := "8000"

# List available recipes.
default:
    @just --list

# Install all dependencies (incl. dev extras) into a uv-managed venv.
install:
    uv sync --extra dev

# Spin up local Postgres via docker compose.
infra:
    docker compose up -d
    @echo "Postgres is starting on localhost:5432 (db: castnote)"

# Tear down local infrastructure.
infra-down:
    docker compose down

# Run the API with hot-reload for local development.
dev:
    uv run uvicorn app.main:app --reload --host {{host}} --port {{port}}

# Run the test suite.
test:
    uv run pytest -q

# Lint and format checks.
lint:
    uv run ruff check app tests
    uv run ruff format --check app tests

# Auto-fix lint + format issues.
fmt:
    uv run ruff check --fix app tests
    uv run ruff format app tests
