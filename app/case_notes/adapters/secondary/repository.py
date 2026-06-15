"""Concrete outbound adapter: SQLAlchemy implementation of the repository port.

``SqlAlchemyCaseNoteRepository`` *implements* the domain's ``CaseNoteRepository``
abstract port. It is the only place in the codebase that knows how Case Notes
are physically stored. Swapping Postgres for another store means writing a new
class against the same port — the domain and use cases stay untouched.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.case_notes.adapters.secondary.orm import CaseNoteORM
from app.case_notes.domain.models import CaseNote
from app.case_notes.domain.ports import CaseNoteRepository


class SqlAlchemyCaseNoteRepository(CaseNoteRepository):
    """Persists :class:`CaseNote` aggregates via an ``AsyncSession``."""

    def __init__(self, session: AsyncSession) -> None:
        # The session is injected per-request by the FastAPI dependency wiring,
        # giving each request its own unit of work.
        self._session = session

    async def add(self, case_note: CaseNote) -> CaseNote:
        row = CaseNoteORM.from_domain(case_note)
        self._session.add(row)
        await self._session.flush()
        return row.to_domain()

    async def get(self, tracking_id: uuid.UUID) -> CaseNote | None:
        row = await self._session.get(CaseNoteORM, tracking_id)
        return row.to_domain() if row is not None else None

    async def list_all(self) -> Sequence[CaseNote]:
        stmt = select(CaseNoteORM).order_by(CaseNoteORM.created_at.desc())
        result = await self._session.execute(stmt)
        return [row.to_domain() for row in result.scalars().all()]

    async def update(self, case_note: CaseNote) -> CaseNote:
        row = await self._session.get(CaseNoteORM, case_note.tracking_id)
        if row is None:
            # The use-case layer guarantees existence before calling update,
            # but we re-add defensively to keep the adapter self-consistent.
            row = CaseNoteORM.from_domain(case_note)
            self._session.add(row)
        else:
            row.current_location = case_note.current_location
            row.status = case_note.status.value
            row.updated_at = case_note.updated_at
        await self._session.flush()
        return row.to_domain()

    async def delete(self, tracking_id: uuid.UUID) -> bool:
        stmt = sa_delete(CaseNoteORM).where(CaseNoteORM.tracking_id == tracking_id)
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0
