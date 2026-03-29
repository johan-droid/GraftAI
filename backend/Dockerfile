# 1. Builder
FROM python:3.12-slim AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

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

# Copy only installed libraries from builder
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

# Using uvicorn for development-ready logs, but gunicorn for scale
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
