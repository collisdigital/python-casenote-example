[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/collisdigital/python-castnote-example)

# NHS Case Notes Tracking API — Hexagonal Architecture Demo

A reference **Case Notes Tracking** feature slice showing how to implement
**Hexagonal Architecture (Ports & Adapters)** inside a single Python package
using modern 2026 patterns: **Python 3.14+**, **FastAPI (async)**,
**Pydantic v2**, **SQLAlchemy 2.0 + asyncpg**, and **`uv`** for dependency
management.

> Case Notes are the physical paper folders of patient information used in NHS
> hospitals. This demo CRUD API tracks where each folder is, and lets you move
> it (e.g. from *Medical Records Library* to *Ward 4*).

## Tech Stack

| Layer                     | Technology                                                          |
| ------------------------- | ------------------------------------------------------------------- |
| Language / runtime        | Python 3.14                                                         |
| Web framework             | [FastAPI](https://fastapi.tiangolo.com/) (async/await)             |
| ASGI server               | [Uvicorn](https://www.uvicorn.org/) (with `standard` extras)       |
| Validation / serialisation| [Pydantic v2](https://docs.pydantic.dev/) + pydantic-settings      |
| ORM / data toolkit        | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (async)              |
| Database                  | [PostgreSQL 16](https://www.postgresql.org/)                        |
| DB driver                 | [asyncpg](https://magicstack.github.io/asyncpg/) (prod) · aiosqlite (tests) |
| Testing                   | [pytest](https://docs.pytest.org/) · pytest-asyncio · [httpx](https://www.python-httpx.org/) |
| Lint / format             | [Ruff](https://docs.astral.sh/ruff/)                                |
| Dependency management      | [uv](https://docs.astral.sh/uv/)                                    |
| Task runner               | [just](https://just.systems/)                                       |
| Local infrastructure       | [Docker](https://www.docker.com/) + Docker Compose                  |

## Quick Start

```bash
just infra      # 1. Start local Postgres (docker compose)
just install    # 2. Install deps into a uv-managed virtualenv
just dev        # 3. Run the API with hot-reload at http://localhost:8000/docs
```

No `just`? The raw equivalents:

```bash
docker compose up -d
uv sync --extra dev
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open the interactive Swagger docs at **http://localhost:8000/docs**.

## Testing

```bash
just test        # or: uv run pytest -q
```

Tests run fully in-memory (SQLite + dependency overrides) — no Postgres needed.

## Architecture

The hexagon keeps NHS business rules at the centre, isolated from frameworks.
Dependencies always point **inwards** toward the pure domain core.

```mermaid
flowchart LR
    HTTP[FastAPI Router<br/>primary adapter] -->|DTOs| SVC[CaseNoteService<br/>use case]
    SVC -->|calls port| PORT{{CaseNoteRepository<br/>outbound port}}
    SVC --> DOM[CaseNote domain model<br/>pure Python]
    PORT -.implemented by.-> REPO[SqlAlchemyCaseNoteRepository<br/>secondary adapter]
    REPO --> PG[(PostgreSQL)]
```

### Layout

```
app/
  main.py                         # Composition root: wires adapters, maps errors
  config.py                       # pydantic-settings configuration
  db.py                           # SQLAlchemy async engine / session plumbing
  case_notes/
    domain/                       # PURE core — no SQLAlchemy, no Pydantic
      models.py                   #   CaseNote + create_case_note() factory
      ports.py                    #   CaseNoteRepository (abc.ABC outbound port)
      exceptions.py               #   Framework-agnostic domain errors
    use_cases/                    # Application layer
      dtos.py                     #   Pydantic v2 request/response DTOs
      services.py                 #   CaseNoteService orchestration
    adapters/
      primary/                    # Inbound (driving) adapter
        router.py                 #   FastAPI APIRouter (async handlers)
        dependencies.py           #   Depends() IoC wiring
      secondary/                  # Outbound (driven) adapter
        orm.py                    #   SQLAlchemy 2.0 Mapped/mapped_column model
        repository.py             #   SqlAlchemyCaseNoteRepository (implements port)
tests/                            # Unit (domain/use-case) + HTTP integration tests
```

### Why the domain core stays pure

The `app/case_notes/domain/` package imports **no** SQLAlchemy and **no**
Pydantic. Those are infrastructure concerns:

- **Pydantic** validates/serialises data at the HTTP edge → it lives in
  `use_cases/dtos.py`, not the domain.
- **SQLAlchemy** maps objects to Postgres rows → it lives in
  `adapters/secondary/`, behind the `CaseNoteRepository` port.

This preserves the Hexagonal principle: business rules depend only on
abstractions, so adapters (Postgres ↔ in-memory, HTTP ↔ CLI) are swappable
without touching the core. The unit tests prove it by running the exact same
`CaseNoteService` against an in-memory fake repository.

### How `Depends` provides Inversion of Control

`adapters/primary/dependencies.py` builds the per-request object graph:

```
Request → AsyncSession → SqlAlchemyCaseNoteRepository → CaseNoteService
```

Route handlers only declare `service: ServiceDep` and FastAPI resolves and
injects a fully-constructed `CaseNoteService`. Handlers never `new` up a
repository or session, so swapping the concrete adapter is a one-line
`app.dependency_overrides[...]` change — exactly what the integration tests do
to substitute SQLite for Postgres.

## API

| Method   | Path                          | Description                        | Success | Errors    |
| -------- | ----------------------------- | ---------------------------------- | ------- | --------- |
| `POST`   | `/case-notes`                 | Create a tracking record           | `201`   | `422`     |
| `GET`    | `/case-notes`                 | List all tracking records          | `200`   | —         |
| `GET`    | `/case-notes/{tracking_id}`   | Fetch one tracking record          | `200`   | `404`     |
| `PATCH`  | `/case-notes/{id}/location`   | Move a case note to a new location | `200`   | `404` `422` |
| `DELETE` | `/case-notes/{tracking_id}`   | Delete a tracking record           | `204`   | `404`     |
| `GET`    | `/health`                     | Liveness probe                     | `200`   | —         |

Response codes are mapped at the HTTP boundary: domain `InvalidCaseNoteError`
becomes `422 Unprocessable Entity` (alongside Pydantic request validation), and
`CaseNoteNotFoundError` becomes `404 Not Found`.

### Interactive docs & schema

| Endpoint        | Description                          |
| --------------- | ------------------------------------ |
| `/docs`         | Swagger UI (interactive API explorer) |
| `/redoc`        | ReDoc API reference                  |
| `/openapi.json` | Raw OpenAPI 3.1 schema               |

Locally these are served at `http://localhost:8000/docs`,
`http://localhost:8000/redoc`, and `http://localhost:8000/openapi.json`.

## Exercising the API with curl

With the server running (`just dev`):

```bash
# Health check
curl http://localhost:8000/health

# Create a tracking record (note the returned tracking_id)
curl -X POST http://localhost:8000/case-notes \
  -H "Content-Type: application/json" \
  -d '{"hospital_number": "RX1234567", "current_location": "Medical Records Library"}'

# List all tracking records
curl http://localhost:8000/case-notes

# Fetch a single record (replace <id> with a real tracking_id)
curl http://localhost:8000/case-notes/<id>

# Move a case note to a new location (and optionally change status)
curl -X PATCH http://localhost:8000/case-notes/<id>/location \
  -H "Content-Type: application/json" \
  -d '{"current_location": "Ward 4", "status": "ON_LOAN"}'

# Delete a tracking record (returns HTTP 204, no body)
curl -X DELETE -i http://localhost:8000/case-notes/<id>
```

A full create → move → delete flow in one go:

```bash
ID=$(curl -s -X POST http://localhost:8000/case-notes \
  -H "Content-Type: application/json" \
  -d '{"hospital_number": "RX1234567", "current_location": "Medical Records Library"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['tracking_id'])")

curl -X PATCH "http://localhost:8000/case-notes/$ID/location" \
  -H "Content-Type: application/json" \
  -d '{"current_location": "Ward 4"}'

curl -X DELETE -i "http://localhost:8000/case-notes/$ID"
```

## Configuration (`.env`)

Settings are loaded by `app/config.py` via pydantic-settings. All variables use
the `CASTNOTE_` prefix and can be set in the environment or in a local `.env`
file (see [.env.example](.env.example)). Unknown variables are ignored.

| Variable                | Default                                                            | Description                                                |
| ----------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------- |
| `CASTNOTE_DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/castnote`  | Async SQLAlchemy database URL (must use an async driver).  |
| `CASTNOTE_ECHO_SQL`     | `false`                                                           | When `true`, logs every SQL statement (useful for debugging). |
| `CASTNOTE_APP_TITLE`    | `NHS Case Notes Tracking API`                                     | Title shown in the OpenAPI docs.                           |

Example `.env`:

```dotenv
CASTNOTE_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/castnote
CASTNOTE_ECHO_SQL=false
CASTNOTE_APP_TITLE=NHS Case Notes Tracking API
```

## Tooling

| Command          | Purpose                                          |
| ---------------- | ------------------------------------------------ |
| `just infra`     | Start local Postgres via docker compose          |
| `just dev`       | Run uvicorn with hot-reload (binds `0.0.0.0`)    |
| `just test`      | Run the pytest suite                             |
| `just lint`      | Ruff lint + format check                         |
| `just fmt`       | Auto-fix lint + format                           |

## Production image

A multi-stage `Dockerfile` builds dependencies with `uv`, then ships a slim,
non-root runtime image with no dev tooling:

```bash
docker build -t castnote-api .
docker run --rm -p 8000:8000 castnote-api
```

## License

MIT — see [LICENSE](LICENSE).