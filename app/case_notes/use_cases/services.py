"""Application service orchestrating Case Note use cases.

The service is the *interactor* layer of the hexagon. It:

1. Accepts validated Pydantic DTOs from the inbound adapter.
2. Drives the pure domain model + factory to apply business rules.
3. Talks to the outbound ``CaseNoteRepository`` **port** (never a concrete DB).
4. Maps domain results back into outbound DTOs.

Because it depends only on the abstract port, the exact same service runs
against Postgres in production and an in-memory fake in unit tests.
"""

from __future__ import annotations

import uuid

from app.case_notes.domain.exceptions import CaseNoteNotFoundError
from app.case_notes.domain.models import create_case_note
from app.case_notes.domain.ports import CaseNoteRepository
from app.case_notes.use_cases.dtos import (
    CaseNoteResponse,
    CreateCaseNoteRequest,
    MoveCaseNoteRequest,
)


class CaseNoteService:
    """Coordinates Case Note workflows over a repository port."""

    def __init__(self, repository: CaseNoteRepository) -> None:
        # The concrete repository is injected (IoC). The service is blissfully
        # unaware of whether it is SQLAlchemy, in-memory, or anything else.
        self._repository = repository

    async def create(self, request: CreateCaseNoteRequest) -> CaseNoteResponse:
        """Create and persist a new tracking record."""
        case_note = create_case_note(
            hospital_number=request.hospital_number,
            current_location=request.current_location,
            status=request.status,
        )
        stored = await self._repository.add(case_note)
        return CaseNoteResponse.from_domain(stored)

    async def get(self, tracking_id: uuid.UUID) -> CaseNoteResponse:
        """Fetch a single tracking record or raise if missing."""
        case_note = await self._repository.get(tracking_id)
        if case_note is None:
            raise CaseNoteNotFoundError(f"No case note found for tracking_id={tracking_id}")
        return CaseNoteResponse.from_domain(case_note)

    async def list_all(self) -> list[CaseNoteResponse]:
        """List every tracking record."""
        records = await self._repository.list_all()
        return [CaseNoteResponse.from_domain(record) for record in records]

    async def move(self, tracking_id: uuid.UUID, request: MoveCaseNoteRequest) -> CaseNoteResponse:
        """Relocate an existing record, applying the domain move rule."""
        existing = await self._repository.get(tracking_id)
        if existing is None:
            raise CaseNoteNotFoundError(f"No case note found for tracking_id={tracking_id}")

        moved = existing.move_to(request.current_location, status=request.status)
        updated = await self._repository.update(moved)
        return CaseNoteResponse.from_domain(updated)

    async def delete(self, tracking_id: uuid.UUID) -> None:
        """Delete a tracking record or raise if it does not exist."""
        removed = await self._repository.delete(tracking_id)
        if not removed:
            raise CaseNoteNotFoundError(f"No case note found for tracking_id={tracking_id}")
