# 1. Builder
FROM python:3.12-slim AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* /app/
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# 2. Runner
FROM python:3.12-slim AS runner
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Security: Don't run as root
RUN addgroup --system --gid 1001 appuser && \
    adduser --system --uid 1001 --gid 1001 appuser

# Copy only installed libraries from builder (simplified for poetry in project root)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY . /app

# Ensure correct permissions
RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV ENV=production
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

# Using gunicorn with uvicorn workers for production-grade robustness
CMD ["gunicorn", "backend.api.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "90"]
