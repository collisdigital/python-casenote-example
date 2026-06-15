"""Outbound port: the persistence contract for the Case Notes domain.

This is a *driven* (secondary) port. The domain declares the abstract async
operations it needs from a data store, but knows nothing about how they are
implemented. SQLAlchemy/Postgres lives behind this interface in the secondary
adapter, so the core depends only on this abstraction (Dependency Inversion).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.case_notes.domain.models import CaseNote


class CaseNoteRepository(ABC):
    """Abstract async repository for persisting :class:`CaseNote` records.

    Concrete implementations (e.g. ``SqlAlchemyCaseNoteRepository``) translate
    these calls into real database I/O. Tests can supply a trivial in-memory
    implementation of the same contract.
    """

    @abstractmethod
    async def add(self, case_note: CaseNote) -> CaseNote:
        """Persist a new tracking record and return the stored aggregate."""

    @abstractmethod
    async def get(self, tracking_id: uuid.UUID) -> CaseNote | None:
        """Return the record for ``tracking_id`` or ``None`` if absent."""

    @abstractmethod
    async def list_all(self) -> Sequence[CaseNote]:
        """Return every tracking record, newest first."""

    @abstractmethod
    async def update(self, case_note: CaseNote) -> CaseNote:
        """Persist changes to an existing record and return it."""

    @abstractmethod
    async def delete(self, tracking_id: uuid.UUID) -> bool:
        """Delete the record. Return ``True`` if a row was removed."""
