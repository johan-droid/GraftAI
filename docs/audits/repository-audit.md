# Repository audit (restructure baseline)

Baseline: `1e41d00`, branch `main`, clean tree at inspection start.
Prior phases (guard, purge, entrypoints, dedup, CI, security, deploy
reconciliation) are in commits `6a98059..1e41d00`.

## Findings carried into this restructure

- Duplicate auth deps unified: `backend/api/deps.py` re-exports
  `backend/auth/schemes.py` (cookie-aware, `require_admin`).
- Cache layers documented as canonical in `backend/utils/cache.py` header:
  `core.redis` (JSON) / `services.cache` (binary) / facade.
- Rate-limit (Lua `utils/rate_limit` for auth/public/billing vs tiered
  `utils/rate_limiter` middleware), calendar (5 layers), AI tools
  (mock vs `_real` gated by `USE_REAL_TOOLS`) intentionally NOT rewired:
  live producers verified, behavior risk too high for a structural pass.
- Legal routes (7 variants with divergent copy incl. Google API clause),
  `lib/api.ts` vs `api-client*.ts` consolidation, model/Alembic merge
  history: documented, deferred for product review.
- Toolchain: `ruff`/`pytest` unavailable locally; CI (blocking ruff,
  backend unit+integration, typecheck, frontend build, docker) is the
  verification gate.

## Unresolved risks

- `infrastructure/docker/compose.yaml` still ships `SECRET_KEY: testsecret` (dev-only;
  must never reach prod).
- `frontend/src/auth.ts:610` dev-secret fallback: verify prod path.
- F-string SQL identifiers (`services/migrations.py`, `execution_agent.py`,
  `data_portability.py`): need allow-list audit.
- SHA256 API-key hashing without pepper: confirm creation/verification parity.
- `local.env` on disk (ignored, uncommitted): never `git add -A` blindly.
