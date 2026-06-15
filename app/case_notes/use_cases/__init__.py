"""Application layer for the Case Notes context.

This layer holds the *use cases* (application services) and the Pydantic DTOs
that form the application boundary. DTOs live here — not in the domain — so the
pure core stays free of Pydantic while the HTTP adapter still gets rich
validation and serialisation at the edge.
"""
