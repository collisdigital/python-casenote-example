"""Domain core for the Case Notes context.

The domain core is the very centre of the hexagon. It expresses NHS business
rules in plain Python and **must never import** infrastructure or framework
libraries (no SQLAlchemy, no Pydantic, no FastAPI).

Keeping the core pure means the rules can be unit-tested in isolation and the
surrounding adapters can be swapped (Postgres -> in-memory, HTTP -> CLI)
without touching a single line of business logic. This is the essence of the
Dependency Inversion Principle that Hexagonal Architecture enforces.
"""
