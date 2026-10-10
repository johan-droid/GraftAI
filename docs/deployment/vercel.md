# Vercel deployment (frontend)

- Project root directory: repository root (build runs `cd frontend && ...`).
- Config: root `vercel.json` is canonical
  (`buildCommand: cd frontend && npm ci && npm run build && node scripts/normalize-sw.js`,
  `installCommand: cd frontend && npm ci`). The stale `frontend/vercel.json`
  was removed.
- Next.js: `output: standalone`, `outputFileTracingRoot` → repo root,
  Serwist service worker (`src/sw.ts` → `public/sw.js`, normalized post-build).
- Backend origin strategy: `BACKEND_URL`/`INTERNAL_BACKEND_URL` (server) take
  precedence over `NEXT_PUBLIC_*`; canonical production host is
  `https://graftai-abu1.onrender.com` (+ `/api/v1` suffix where needed).
  `next.config.ts` rewrites proxy `/auth/*`, `/health`, and `/api/*` fallback.
- Env (Vercel project): `BACKEND_URL`, `NEXT_PUBLIC_API_BASE_URL`
  (`.../api/v1`), `NEXT_PUBLIC_BACKEND_URL`, `NEXT_PUBLIC_APP_URL`,
  `AUTH_URL`/`NEXTAUTH_URL`, OAuth client IDs/secrets. Never put private
  credentials in `NEXT_PUBLIC_*`.
