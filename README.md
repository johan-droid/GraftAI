# GraftAI

AI-based scheduling and booking system.

## Stack

- **Frontend:** Next.js 16 (App Router), TypeScript, Tailwind CSS, npm — deployed on **Vercel**
- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), Celery — deployed on **Render** (API + worker)
- **Data:** PostgreSQL, Redis

## Quick Start

See [docs/development/local-setup.md](./docs/development/local-setup.md).

```bash
# Local infra (Postgres + Redis)
docker compose up -d db redis

# Backend: pip install -r backend/requirements.txt
# Frontend: cd frontend && npm ci
```

## Docs

- [Documentation index](./docs/README.md)
- [Architecture overview](./docs/architecture/overview.md)
- [API overview](./docs/api/overview.md)
- [Vercel deployment](./docs/deployment/vercel.md)
- [Render deployment](./docs/deployment/render.md)

## Project layout

- `frontend/` — Next.js app (Vercel)
- `backend/` — FastAPI API + Celery worker (Render)
- `docs/` — canonical documentation
- `infrastructure/docker/compose.yaml` — local Postgres + Redis
- `scripts/` — dev and check helpers
