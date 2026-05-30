# GraftAI

GraftAI is an AI-based scheduling and booking system.

## Stack
- Frontend: Next.js 16 (App Router), TypeScript, Tailwind CSS, pnpm
- Backend: Python 3.12, FastAPI, SQLAlchemy (async), Celery, Poetry
- Database: PostgreSQL, Redis

## Quick Start
```
docker-compose up
```

## Development

- Run the backend in a venv (recommended):

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate
pip install -r backend/requirements.txt
```

- Run unit tests:

```bash
# Install test deps if needed
pip install pytest pytest-asyncio
python -m pytest -q
```

Run only the rate limiter tests:

```bash
python -m pytest backend/tests/unit/test_rate_limiter.py -q
```
