"""Domain-level exceptions for the Case Notes context.

These are framework-agnostic errors. The primary HTTP adapter is responsible
for translating them into transport-specific responses (e.g. HTTP 404/422),
which keeps the domain ignorant of how it is being consumed.
"""

from __future__ import annotations


class CaseNoteError(Exception):
    """Base class for every Case Notes domain error."""


class InvalidCaseNoteError(CaseNoteError):
    """Raised when a domain invariant is violated (bad status, location, etc.)."""


class CaseNoteNotFoundError(CaseNoteError):
    """Raised when a tracking record cannot be located by its identifier."""
