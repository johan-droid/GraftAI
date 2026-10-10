# API overview

- Entrypoint: `backend/api/main.py:create_app()`; module-level `app`.
  Routers registered manually under `/api/v1` (plus `/api/v1/audit`);
  legacy `/api/* → /api/v1/*` 308 redirects retained.
- Auth: OAuth (Google/Microsoft), session + JWT, MFA/TOTP, API keys with
  tiered rate limits. Canonical deps: `backend/auth/schemes.py`
  (`get_current_user`, `get_current_user_id`, `require_admin`).
- Contracts: request/response models colocated in route modules and
  `backend/schemas/*`; see `docs/auth_openapi.yaml` (auth subset) and
  `docs/RATE_LIMITING.md` (API-key tiers/hashing).
- Frontend clients: `frontend/src/lib/api-client.ts` (base, `API_BASE_URL`
  normalization) wrapped by `api-client-enhanced.ts` (retry/queue/offline);
  `backend.ts` resolves server-side origin. WebSocket telemetry via
  `lib/ai-api.ts` → `/api/v1/monitoring/ws`.
- Errors: global handlers in `backend/utils/error_handlers.py`; rate-limit
  429s with `Retry-After`; booking/webhook idempotency where implemented.
