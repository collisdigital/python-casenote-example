"""Pydantic v2 DTOs — the application boundary contracts.

These models validate and serialise data crossing the edge of the application.
They are deliberately kept **out of the domain core**: Pydantic is an
infrastructure concern (HTTP/JSON validation), and letting it leak into the
domain would couple business rules to a serialisation library. Instead the
use-case services translate between these DTOs and the pure ``CaseNote`` model.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.case_notes.domain.models import CaseNote, TrackingStatus


class CreateCaseNoteRequest(BaseModel):
    """Inbound DTO for creating a new tracking record."""

    model_config = ConfigDict(extra="forbid")

    hospital_number: str = Field(
        ...,
        examples=["RX1234567"],
        description="Local hospital number: 1-3 letters followed by 6-10 digits.",
    )
    current_location: str = Field(
        ...,
        examples=["Medical Records Library"],
        description="Physical location where the case note currently resides.",
    )
    status: TrackingStatus = Field(
        default=TrackingStatus.FILED,
        description="Initial tracking lifecycle status.",
    )


class MoveCaseNoteRequest(BaseModel):
    """Inbound DTO for relocating / updating an existing tracking record."""

    model_config = ConfigDict(extra="forbid")

    current_location: str = Field(
        ...,
        examples=["Ward 4"],
        description="New physical location to move the case note to.",
    )
    status: TrackingStatus | None = Field(
        default=None,
        description="Optional new tracking status to apply during the move.",
    )


class CaseNoteResponse(BaseModel):
    """Outbound DTO returned to HTTP clients."""

    model_config = ConfigDict(from_attributes=True)

    tracking_id: uuid.UUID
    hospital_number: str
    current_location: str
    status: TrackingStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, case_note: CaseNote) -> CaseNoteResponse:
        """Map a pure domain ``CaseNote`` into a serialisable response DTO.

        This explicit mapping is the translation seam that keeps Pydantic out
        of the domain: the core hands back a plain object and the application
        layer adapts it to the transport contract.
        """
        return cls(
            tracking_id=case_note.tracking_id,
            hospital_number=case_note.hospital_number,
            current_location=case_note.current_location,
            status=case_note.status,
            created_at=case_note.created_at,
            updated_at=case_note.updated_at,
        )
