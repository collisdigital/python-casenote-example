"""Case Notes feature slice.

This package demonstrates Hexagonal Architecture (Ports & Adapters) for a single
NHS-style domain context: tracking the physical location of paper *case notes*
as they move around a hospital.

Layer map::

    domain/              <- Pure Python core (no framework imports)
    use_cases/           <- Application services + Pydantic DTOs
    adapters/primary/    <- Inbound HTTP adapter (FastAPI router)
    adapters/secondary/  <- Outbound infrastructure adapter (SQLAlchemy)
"""
