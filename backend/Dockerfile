FROM python:3.12-slim-bookworm

LABEL maintainer="GraftAI Engineering <ops@graftai.tech>"

WORKDIR /app

# Install runtime/build deps
# Install system deps and pip, then install Python requirements globally
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-pip \
    curl \
    ca-certificates \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements and install globally
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
  && python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy application code under the backend package path so imports like
# backend.api.main resolve correctly.
COPY . /app/backend

# Security: Dedicated non-root user
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid 1001 -m -s /bin/bash appuser

# Ensure correct permissions
RUN chown -R appuser:appgroup /app

USER appuser

# Environment Configuration
ENV PYTHONUNBUFFERED=1
ENV PYTHONUNBUFFERED=1
ENV ENV=production
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint: run gunicorn with the system Python (requirements are installed globally)
# Use shell form so $PORT expands from the environment
CMD ["sh", "-c", "python -m gunicorn backend.api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 4 --timeout 120"]
