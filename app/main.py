"""Composition root for the NHS Case Notes Tracking API.

``main.py`` is deliberately disciplined. Its only jobs are to:

1. Build the async SQLAlchemy engine + session-pool once at startup.
2. Mount the Case Notes inbound HTTP adapter (router).
3. Translate domain exceptions into HTTP responses at the edge.
4. Expose OpenAPI/Swagger docs.

No business logic lives here — this is purely where the hexagon's adapters are
plugged into the application core.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.case_notes.adapters.primary.router import router as case_notes_router
from app.case_notes.domain.exceptions import (
    CaseNoteNotFoundError,
    InvalidCaseNoteError,
)
from app.config import get_settings
from app.db import Base, create_engine, create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage the async engine lifecycle and create tables on startup.

    For this demo we create tables via ``create_all``. A production NHS service
    would manage schema with Alembic migrations instead.
    """
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=settings.echo_sql)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    """Application factory — builds and wires the FastAPI app."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_title,
        version="0.1.0",
        summary="Hexagonal Architecture demo for tracking NHS paper case notes.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    _register_exception_handlers(app)

    @app.get("/health", tags=["System"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(case_notes_router)
    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Map pure domain errors to HTTP responses at the boundary.

    The domain raises framework-agnostic exceptions; this is the single place
    that knows how those map onto HTTP status codes, keeping the core unaware
    of the transport.
    """

    @app.exception_handler(CaseNoteNotFoundError)
    async def _not_found(_: Request, exc: CaseNoteNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InvalidCaseNoteError)
    async def _invalid(_: Request, exc: InvalidCaseNoteError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})


app = create_app()
