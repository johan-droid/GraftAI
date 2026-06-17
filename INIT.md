# Execution Init: Agent Instructions & Production Readiness

**Date:** 2026-06-17  
**Branch:** `ops/agent-instructions`  
**Agent:** OpenCode (deepseek-v4-flash-free)

## Scope

1. **AGENTS.md** — Rewritten compact instruction file for future agent sessions. Sources: config files, test fixtures, CI workflows, render.yaml, Dockerfile, directory audit.

2. **PRODUCTION_READINESS.md** — Standalone production-refactoring playbook (race conditions, security, caching, resilience, testing). To be used by agents executing Phase 1–5 fixes.

## Key Findings During Investigation

- README says "pnpm" but lockfile is `package-lock.json` (npm).
- `pyproject.toml` is in `backend/` not root. Docker/Render use `requirements.txt`.
- `asyncio_mode = auto` in backend pytest.ini — no `@pytest.mark.asyncio` needed.
- Tests use SQLite in-memory with SAVEPOINT isolation, not Postgres.
- Rich test fixtures in `backend/tests/conftest.py`.
- All router registration is manual in `backend/api/main.py` `create_app()`.
- TD-9 (Redis-backed conversation history) is the only remaining technical debt.
- Production SECRET_KEY validation already implemented in `backend/api/main.py:65-67`.
- CSP nonce injection in `frontend/middleware.ts`.

## Files Created

| File | Purpose |
|------|---------|
| `AGENTS.md` | Compact agent onboarding guide |
| `PRODUCTION_READINESS.md` | Refactoring execution plan |
| `INIT.md` | This file — execution tracker |

## Branch Strategy

All changes on `ops/agent-instructions`. Never merge to `main` without review.
