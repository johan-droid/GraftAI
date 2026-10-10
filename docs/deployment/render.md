# Render deployment (backend)

Defined in root `render.yaml`:

- `graftai-api` (web, Python, Oregon, starter): build
  `pip install -r backend/requirements.txt`; start
  `python -m uvicorn backend.api.main:app --host 0.0.0.0 --port "$PORT" --proxy-headers`
  with `PYTHONPATH=.`; health check `/health`.
- `graftai-celery-worker` (worker): same build; start
  `celery -A backend.core.celery_app worker --loglevel=info --concurrency=4`.
  Queues: email, calendar, webhook, workflow, reminder; beat: sync 300s,
  reminders 60s, workflows 60s, webhook-retry 300s.
- `graftai-db` (Postgres starter). Redis is external: create in dashboard,
  set `REDIS_URL` on both services (see `render.yaml:137-138`).
- Required prod env: `SECRET_KEY` (≥32 chars, not a default),
  `DATABASE_URL` (from database), `FRONTEND_URL`, `NEXT_PUBLIC_API_URL`,
  `REDIS_URL`; OAuth callbacks point at
  `https://graftai-abu1.onrender.com/api/v1/auth/*/callback`.
- Alembic migrations live in `backend/alembic/versions/`; startup migration
  logic is in `backend/api/main.py` + `backend/services/migrations.py`.
