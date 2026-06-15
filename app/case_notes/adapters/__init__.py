"""Adapters connect the application to the outside world.

* ``primary``   — *driving* adapters (inbound): things that call into the app,
  e.g. the FastAPI HTTP router.
* ``secondary`` — *driven* adapters (outbound): things the app calls out to,
  e.g. the SQLAlchemy/Postgres repository implementation.
"""
