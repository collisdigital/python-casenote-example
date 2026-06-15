"""SQLAlchemy 2.0 declarative base and async engine/session plumbing.

This module is pure infrastructure. Nothing in the domain core imports it; the
dependency arrow points *inwards* from here to the domain, never the reverse.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models in this project."""


def create_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Build a pooled async engine for the given database URL."""
    return create_async_engine(database_url, echo=echo, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build an ``async_sessionmaker`` bound to ``engine``."""
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield a session, committing on success and rolling back on error.

    Used by the FastAPI dependency layer to provide a unit-of-work per request.
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
