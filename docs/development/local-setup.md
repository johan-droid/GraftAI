# Local setup

Prereqs: Python 3.12, Node 22, npm, Docker (for Postgres + Redis only).

```bash
# 1. Local infra
docker compose up -d db redis

# 2. Backend (from repo root)
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1 | macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # fill secrets, never commit

# 3. Frontend
cd frontend && npm ci

# 4. Run
# Terminal 1: uvicorn backend.api.main:app --reload   (from repo root, venv active)
# Terminal 2: cd frontend && npm run dev
```

Tests: `python -m pytest -q` (root config; manual billing tests skip unless
`RUN_MANUAL_BILLING_TESTS=1`). Frontend: `npx tsc --noEmit`, single
`src/**/*.test.ts` via `npm test`.

Destructive DB scripts refuse in production and require
`ALLOW_DESTRUCTIVE_DB_SCRIPTS=1` outside it.
