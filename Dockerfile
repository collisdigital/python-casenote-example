# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1: builder — resolve and install dependencies into a virtualenv using uv
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# uv: fast, reproducible Python dependency management.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install dependencies first (cached layer) using only the lock + manifest.
COPY pyproject.toml ./
COPY uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

# Now install the project itself.
COPY app ./app
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

# ---------------------------------------------------------------------------
# Stage 2: runtime — slim image, non-root, no build bloat
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Create an unprivileged user to run the app.
RUN groupadd --system app && useradd --system --gid app --create-home app

WORKDIR /app

# Copy only the resolved virtualenv and application code from the builder.
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/app /app/app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER app
EXPOSE 8000

# Bind to 0.0.0.0 so container/Codespaces port-forwarding works.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
