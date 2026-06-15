"""Unit tests for the application service using the in-memory repository fake."""

from __future__ import annotations

import uuid

import pytest
from app.case_notes.domain.exceptions import CaseNoteNotFoundError
from app.case_notes.domain.models import TrackingStatus
from app.case_notes.use_cases.dtos import (
    CreateCaseNoteRequest,
    MoveCaseNoteRequest,
)
from app.case_notes.use_cases.services import CaseNoteService

from tests.conftest import InMemoryCaseNoteRepository


@pytest.fixture
def service(in_memory_repository: InMemoryCaseNoteRepository) -> CaseNoteService:
    return CaseNoteService(in_memory_repository)


async def test_create_then_get(service: CaseNoteService) -> None:
    created = await service.create(
        CreateCaseNoteRequest(
            hospital_number="RX1234567", current_location="Medical Records Library"
        )
    )
    fetched = await service.get(created.tracking_id)
    assert fetched.tracking_id == created.tracking_id
    assert fetched.current_location == "Medical Records Library"


async def test_move_updates_location_and_status(service: CaseNoteService) -> None:
    created = await service.create(
        CreateCaseNoteRequest(
            hospital_number="RX1234567", current_location="Medical Records Library"
        )
    )
    moved = await service.move(
        created.tracking_id,
        MoveCaseNoteRequest(current_location="Ward 4", status=TrackingStatus.ON_LOAN),
    )
    assert moved.current_location == "Ward 4"
    assert moved.status is TrackingStatus.ON_LOAN


async def test_get_missing_raises(service: CaseNoteService) -> None:
    with pytest.raises(CaseNoteNotFoundError):
        await service.get(uuid.uuid4())


async def test_delete_then_missing(service: CaseNoteService) -> None:
    created = await service.create(
        CreateCaseNoteRequest(hospital_number="RX1234567", current_location="Ward 4")
    )
    await service.delete(created.tracking_id)
    with pytest.raises(CaseNoteNotFoundError):
        await service.get(created.tracking_id)


async def test_delete_missing_raises(service: CaseNoteService) -> None:
    with pytest.raises(CaseNoteNotFoundError):
        await service.delete(uuid.uuid4())
