"""Unit tests for the pure domain core — no DB, no HTTP, no frameworks."""

from __future__ import annotations

import uuid

import pytest
from app.case_notes.domain.exceptions import InvalidCaseNoteError
from app.case_notes.domain.models import (
    TrackingStatus,
    create_case_note,
)


def test_create_case_note_normalises_hospital_number() -> None:
    note = create_case_note(hospital_number=" rx1234567 ", current_location="Ward 4")
    assert note.hospital_number == "RX1234567"
    assert note.current_location == "Ward 4"
    assert note.status is TrackingStatus.FILED
    assert isinstance(note.tracking_id, uuid.UUID)


@pytest.mark.parametrize("bad", ["", "123456", "TOOLONG12345678901", "AB12"])
def test_invalid_hospital_number_rejected(bad: str) -> None:
    with pytest.raises(InvalidCaseNoteError):
        create_case_note(hospital_number=bad, current_location="Ward 4")


def test_empty_location_rejected() -> None:
    with pytest.raises(InvalidCaseNoteError):
        create_case_note(hospital_number="RX1234567", current_location="   ")


def test_invalid_status_rejected() -> None:
    with pytest.raises(InvalidCaseNoteError):
        create_case_note(
            hospital_number="RX1234567",
            current_location="Ward 4",
            status="NOT_A_STATUS",
        )


def test_move_to_returns_new_immutable_instance() -> None:
    original = create_case_note(
        hospital_number="RX1234567", current_location="Medical Records Library"
    )
    moved = original.move_to("Ward 4", status=TrackingStatus.ON_LOAN)

    assert moved is not original
    assert moved.current_location == "Ward 4"
    assert moved.status is TrackingStatus.ON_LOAN
    assert moved.tracking_id == original.tracking_id
    # Original is frozen / unchanged.
    assert original.current_location == "Medical Records Library"
    assert moved.updated_at >= original.updated_at


def test_move_to_empty_location_rejected() -> None:
    note = create_case_note(hospital_number="RX1234567", current_location="Ward 4")
    with pytest.raises(InvalidCaseNoteError):
        note.move_to("")
