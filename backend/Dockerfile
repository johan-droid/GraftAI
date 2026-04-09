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
LABEL maintainer="GraftAI Engineering <ops@graftai.tech>"
WORKDIR /app

# Install runtime dependencies ONLY
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Security: Dedicated non-root user
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid 1001 -m -s /bin/bash appuser

# Copy virtual environment and app code
COPY --from=builder /app/.venv /app/.venv
COPY . /app

# Ensure correct permissions
RUN chown -R appuser:appgroup /app
USER appuser

# Environment Configuration
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV ENV=production
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

# Health Check for automated orchestration failover
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Simplified Monolith Entrypoint:
CMD ["sh", "-c", "gunicorn backend.api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 4 --timeout 120"]
