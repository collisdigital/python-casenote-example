"""Pure-Python domain model for a tracked NHS Case Note.

No SQLAlchemy. No Pydantic. No FastAPI. Just Python and business rules.

A ``CaseNote`` represents the *tracking record* for a physical paper folder of
patient information. The record knows where the folder currently is, what its
tracking lifecycle status is, and enforces NHS-style invariants such as a valid
hospital number format and a non-empty location.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum

from app.case_notes.domain.exceptions import InvalidCaseNoteError

# NHS numbers / local hospital numbers vary, but for this demo we enforce a
# simple, deterministic format so the rule is easy to reason about and test.
_HOSPITAL_NUMBER_PATTERN = re.compile(r"^[A-Z]{1,3}\d{6,10}$")


class TrackingStatus(StrEnum):
    """Lifecycle of a case note tracking record.

    ``StrEnum`` keeps the value a plain string at the boundary while still
    giving the domain a closed set of valid states to validate against.
    """

    IN_TRANSIT = "IN_TRANSIT"
    FILED = "FILED"
    ON_LOAN = "ON_LOAN"
    ARCHIVED = "ARCHIVED"


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class CaseNote:
    """A tracking record for a physical NHS case note folder.

    The dataclass is ``frozen`` so the model is immutable: state transitions
    (e.g. moving location) return a *new* instance rather than mutating in
    place. This makes the domain easier to reason about and test.

    Prefer the :func:`create_case_note` factory over calling this constructor
    directly so that invariants are always enforced.
    """

    tracking_id: uuid.UUID
    hospital_number: str
    current_location: str
    status: TrackingStatus
    created_at: datetime
    updated_at: datetime

    def move_to(self, new_location: str, *, status: TrackingStatus | None = None) -> CaseNote:
        """Return a new record relocated to ``new_location``.

        Encapsulates the relocation rule: a case note can never be moved to an
        empty/blank location. Optionally transitions the tracking status.
        """
        cleaned = _validate_location(new_location)
        return replace(
            self,
            current_location=cleaned,
            status=status or self.status,
            updated_at=_now(),
        )

    def with_status(self, status: TrackingStatus) -> CaseNote:
        """Return a new record with an updated tracking status."""
        return replace(self, status=status, updated_at=_now())


def _validate_hospital_number(value: str) -> str:
    candidate = (value or "").strip().upper()
    if not _HOSPITAL_NUMBER_PATTERN.match(candidate):
        raise InvalidCaseNoteError(
            "hospital_number must look like 'RX1234567' (1-3 letters followed by 6-10 digits)"
        )
    return candidate


def _validate_location(value: str) -> str:
    candidate = (value or "").strip()
    if not candidate:
        raise InvalidCaseNoteError("current_location must not be empty")
    if len(candidate) > 120:
        raise InvalidCaseNoteError("current_location must be 120 characters or fewer")
    return candidate


def _coerce_status(value: TrackingStatus | str) -> TrackingStatus:
    try:
        return TrackingStatus(value)
    except ValueError as exc:
        valid = ", ".join(s.value for s in TrackingStatus)
        raise InvalidCaseNoteError(f"status must be one of: {valid}") from exc


def create_case_note(
    *,
    hospital_number: str,
    current_location: str,
    status: TrackingStatus | str = TrackingStatus.FILED,
    tracking_id: uuid.UUID | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> CaseNote:
    """Factory that builds a valid :class:`CaseNote` or raises.

    Centralising construction here guarantees every ``CaseNote`` in the system
    satisfies NHS invariants, regardless of which adapter created it. Adapters
    (HTTP, DB) call this factory rather than reconstructing invariants
    themselves, keeping the rules in exactly one place.
    """
    now = _now()
    return CaseNote(
        tracking_id=tracking_id or uuid.uuid4(),
        hospital_number=_validate_hospital_number(hospital_number),
        current_location=_validate_location(current_location),
        status=_coerce_status(status),
        created_at=created_at or now,
        updated_at=updated_at or now,
    )
