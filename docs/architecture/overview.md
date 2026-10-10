# Architecture overview

## Boundaries

- `frontend/` — Next.js 16 App Router. Owns pages, layouts, UI components,
  client state, typed API clients, frontend validation, static assets,
  service worker. Deployed on Vercel.
- `backend/` — FastAPI. Owns business rules, API schemas, authz, persistence,
  migrations, scheduling correctness, background tasks, integrations,
  logging/monitoring. Deployed on Render (web API + Celery worker).

No business logic is duplicated between layers. Next.js route handlers under
`frontend/src/app/api/` are narrowly scoped (NextAuth callbacks, diagnostics)
and must not re-implement FastAPI behavior.

## Data flow

Browser → Vercel (Next.js) → Render API (`/api/v1/*`, canonical host
`https://graftai-abu1.onrender.com`) → PostgreSQL / Redis.
Long-running work (email, calendar sync, webhooks, workflows, reminders)
is enqueued to Celery queues and executed by the Render worker service.

## Key modules

- API factory + routers: `backend/api/main.py` (`create_app`), `backend/api/*`,
  `backend/auth/routes.py`
- Auth deps (canonical): `backend/auth/schemes.py`, re-exported by
  `backend/api/deps.py`
- Persistence: `backend/models/*`, Alembic `backend/alembic/versions/`
- Queues: `backend/core/celery_app.py`, `backend/tasks/*`,
  `backend/services/task_queue.py`, `backend/services/workflow_engine.py`
- Frontend API layer: `frontend/src/lib/api-client.ts`,
  `frontend/src/lib/api-client-enhanced.ts`, `frontend/src/lib/backend.ts`
  (server), `frontend/next.config.ts` rewrites
