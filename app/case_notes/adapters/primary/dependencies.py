"""FastAPI dependency wiring — the Inversion of Control (IoC) seam.

FastAPI's ``Depends`` is a lightweight IoC container. Each function here
*provides* a collaborator, and FastAPI resolves the graph per request:

    request -> AsyncSession -> SqlAlchemyCaseNoteRepository -> CaseNoteService

Route handlers declare *what* they need (a ``CaseNoteService``) and FastAPI
injects a fully-constructed instance. Handlers never construct repositories or
sessions themselves, so the concrete Postgres adapter can be swapped (e.g. for
an in-memory fake in tests) by overriding a single dependency.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.case_notes.adapters.secondary.repository import SqlAlchemyCaseNoteRepository
from app.case_notes.domain.ports import CaseNoteRepository
from app.case_notes.use_cases.services import CaseNoteService
from app.db import get_session


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    """Pull the app-wide session factory off ``app.state`` (set in main.py)."""
    return request.app.state.session_factory


async def get_db_session(
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncIterator[AsyncSession]:
    """Yield a per-request unit-of-work session."""
    async for session in get_session(session_factory):
        yield session


def get_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CaseNoteRepository:
    """Provide the concrete repository, typed as the abstract port.

    The return annotation is the *port* (``CaseNoteRepository``), reinforcing
    that callers depend on the abstraction, not the SQLAlchemy implementation.
    """
    return SqlAlchemyCaseNoteRepository(session)


def get_service(
    repository: Annotated[CaseNoteRepository, Depends(get_repository)],
) -> CaseNoteService:
    """Provide the application service with its repository injected."""
    return CaseNoteService(repository)


# Reusable annotated alias so route signatures stay clean and declarative.
ServiceDep = Annotated[CaseNoteService, Depends(get_service)]
