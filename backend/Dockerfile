# Use highly efficient UV-based multi-stage build
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# 1. Install Build Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy dependency files first for caching
COPY pyproject.toml requirements.txt* /app/
# Install dependencies into /app/.venv
RUN uv sync --no-dev --no-install-project

# 2. Production Runner
FROM python:3.12-slim-bookworm AS runner
WORKDIR /app

# Install runtime dependencies ONLY
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Security: Dedicated non-root user
RUN addgroup --system --gid 1001 appuser && \
    adduser --system --uid 1001 --gid 1001 appuser

# Copy virtual environment and app code
COPY --from=builder /app/.venv /app/.venv
COPY . /app

# Ensure correct permissions
RUN chown -R appuser:appuser /app
USER appuser

# Environment Configuration
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV ENV=production
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

# Default CMD (Overridden by Render for the Worker instance)
CMD ["gunicorn", "backend.api.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "90"]
