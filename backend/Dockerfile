FROM python:3.12-slim as base
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* /app/
# Ensure pyyaml uses pure-Python fallback if C extension build fails in cloud CI
ENV PYTHON_PYYAML_NO_EXTENSIONS=1
RUN pip install --upgrade pip setuptools wheel Cython poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy repository root into /app so backend package is available as /app/backend
COPY . /app

# Ensure the Python import root can resolve backend package at container runtime
ENV PYTHONUNBUFFERED=1
ENV ENV=production
ENV PYTHONPATH=/app

EXPOSE 8000

CMD uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4 --proxy-headers
