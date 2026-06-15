"""SQLAlchemy 2.0 ORM model for the Case Notes Postgres table.

This ORM model is intentionally separate from the pure domain ``CaseNote``.
The domain object expresses *behaviour and rules*; this object expresses *table
structure*. Keeping them apart means a schema change here never forces a change
to business logic in the core, and the domain never imports SQLAlchemy.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.case_notes.domain.models import CaseNote, TrackingStatus
from app.db import Base


class CaseNoteORM(Base):
    """Row mapping for the ``case_notes`` table in the NHS Postgres schema."""

    __tablename__ = "case_notes"

    tracking_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    hospital_number: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    current_location: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def to_domain(self) -> CaseNote:
        """Rehydrate a pure domain aggregate from this ORM row."""
        return CaseNote(
            tracking_id=self.tracking_id,
            hospital_number=self.hospital_number,
            current_location=self.current_location,
            status=TrackingStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, case_note: CaseNote) -> CaseNoteORM:
        """Build an ORM row from a pure domain aggregate."""
        return cls(
            tracking_id=case_note.tracking_id,
            hospital_number=case_note.hospital_number,
            current_location=case_note.current_location,
            status=case_note.status.value,
            created_at=case_note.created_at,
            updated_at=case_note.updated_at,
        )
