"""Shared pytest fixtures.

Provides:
* ``InMemoryCaseNoteRepository`` — a fast fake implementing the outbound port,
  used to unit-test the service without a database.
* An ``httpx.AsyncClient`` wired to the real FastAPI app but backed by an
  in-memory SQLite database via a dependency override (no Postgres needed).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Sequence

import pytest
import pytest_asyncio
from app.case_notes.adapters.primary.dependencies import get_db_session
from app.case_notes.domain.models import CaseNote
from app.case_notes.domain.ports import CaseNoteRepository
from app.db import Base, create_engine
from app.main import create_app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class InMemoryCaseNoteRepository(CaseNoteRepository):
    """Dict-backed fake implementing the repository port for unit tests."""

    def __init__(self) -> None:
        self._store: dict[uuid.UUID, CaseNote] = {}

    async def add(self, case_note: CaseNote) -> CaseNote:
        self._store[case_note.tracking_id] = case_note
        return case_note

    async def get(self, tracking_id: uuid.UUID) -> CaseNote | None:
        return self._store.get(tracking_id)

    async def list_all(self) -> Sequence[CaseNote]:
        return sorted(self._store.values(), key=lambda c: c.created_at, reverse=True)

    async def update(self, case_note: CaseNote) -> CaseNote:
        self._store[case_note.tracking_id] = case_note
        return case_note

    async def delete(self, tracking_id: uuid.UUID) -> bool:
        return self._store.pop(tracking_id, None) is not None


@pytest.fixture
def in_memory_repository() -> InMemoryCaseNoteRepository:
    return InMemoryCaseNoteRepository()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Async HTTP client against the real app, backed by in-memory SQLite."""
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app = create_app()

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # IoC in action: replace the Postgres-backed session with SQLite for tests.
    app.dependency_overrides[get_db_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await engine.dispose()
