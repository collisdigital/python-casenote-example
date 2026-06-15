"""Inbound HTTP adapter: FastAPI ``APIRouter`` for Case Notes tracking.

These async handlers are *thin*. They do no business logic — they simply accept
validated DTOs, delegate to the injected ``CaseNoteService`` (resolved via
``Depends``), and return DTOs. All NHS rules live in the domain; all I/O lives
in the secondary adapter. This is the inbound side of the hexagon.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.case_notes.adapters.primary.dependencies import ServiceDep
from app.case_notes.use_cases.dtos import (
    CaseNoteResponse,
    CreateCaseNoteRequest,
    MoveCaseNoteRequest,
)

router = APIRouter(prefix="/case-notes", tags=["Case Notes"])


@router.post(
    "",
    response_model=CaseNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a case note tracking record",
)
async def create_case_note(payload: CreateCaseNoteRequest, service: ServiceDep) -> CaseNoteResponse:
    """Register a new physical case note in the tracking system."""
    return await service.create(payload)


@router.get(
    "",
    response_model=list[CaseNoteResponse],
    summary="List all case note tracking records",
)
async def list_case_notes(service: ServiceDep) -> list[CaseNoteResponse]:
    """Return every tracking record, newest first."""
    return await service.list_all()


@router.get(
    "/{tracking_id}",
    response_model=CaseNoteResponse,
    summary="Fetch a single tracking record",
)
async def get_case_note(tracking_id: uuid.UUID, service: ServiceDep) -> CaseNoteResponse:
    """Return the tracking record identified by ``tracking_id``."""
    return await service.get(tracking_id)


@router.patch(
    "/{tracking_id}/location",
    response_model=CaseNoteResponse,
    summary="Move a case note to a new location",
)
async def move_case_note(
    tracking_id: uuid.UUID, payload: MoveCaseNoteRequest, service: ServiceDep
) -> CaseNoteResponse:
    """Relocate a case note, e.g. from 'Medical Records Library' to 'Ward 4'."""
    return await service.move(tracking_id, payload)


@router.delete(
    "/{tracking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tracking record",
)
async def delete_case_note(tracking_id: uuid.UUID, service: ServiceDep) -> None:
    """Remove a case note tracking record from the system."""
    await service.delete(tracking_id)
