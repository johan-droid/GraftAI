# GraftAI

End-to-end AI scheduling and auth platform (FastAPI backend + Next.js frontend) with SSO + passwordless + MFA + FIDO2 + Auth0 JWT validation.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Features](#features)
- [Backend](#backend)
  - [Setup](#backend-setup)
  - [Configuration](#backend-configuration)
  - [Routes](#backend-routes)
  - [Auth0 Integration](#auth0-integration)
- [Frontend](#frontend)
  - [Setup](#frontend-setup)
  - [Pages & Flow](#frontend-pages--flow)
  - [Routing and Guard](#routing-and-guard)
- [Running the App](#running-the-app)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contribution](#contribution)
- [Licensing](#licensing)

---

## Project Overview

GraftAI is a modern scheduling platform integrating user authentication, role-based access, and AI support services. It is structured as:

- `backend/`: Python FastAPI microservice with Auth0, SSO, passwordless, MFA, FIDO2, and API endpoints.
- `frontend/`: Next.js (App Router) mobile-first interface built with TypeScript and Tailwind.

The project includes secure token flows, session refresh, and complete frontend/backend integration.

---

## Architecture

- FastAPI backend on `http://localhost:8000`
- Next.js frontend on `http://localhost:3000`
- Auth is handled via JWT
  - Local HS256 fallback (`SECRET_KEY`)
  - Auth0 RS256 if `AUTH0_DOMAIN` and `AUTH0_AUDIENCE` are configured
- SSO routes proxy an OAuth2 provider (e.g., GitHub) through `backend/services/sso.py`
- Frontend stores token in localStorage and cookie (for middleware gating)

---

## Features

### Auth

- Username/password token generation (`/auth/token`)
- SSO (OAuth2-style) with state redirect support
- Passwordless request and verification
- MFA setup + verification
- FIDO2 registration and verification endpoints
- DID issuance and verification via FIDO2+DID service
- API route-based role/attribute checks

### Security

- `backend/auth/schemes.py` includes token decoding for both local and Auth0 flows
- `middleware.ts` route guard for `/dashboard`
- `apiFetch` helper auto-redirects to login on 401/403
- automatic token expiry detection + invalidation

### Frontend (Mobile-first)

- Login `/auth/login` and SSO button
- MFA `/auth/mfa`
- SSO `/auth/sso` (redirect-to next state)
- Callback `/auth-callback` (receives `code`, `state`, gets JWT and follows `redirect_to`)
- Auth guard on `/dashboard`
- Dark/Light theming and responsive styling

---

## Backend

### Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Configuration

Create `.env` in `backend` (copy from `.env.example` if available) with these core keys:

```env
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=...
SECRET_KEY=...
JWT_SECRET=...
SESSION_EXPIRE_MINUTES=60
AUTH0_DOMAIN=nextgen-scheduler.eu.auth0.com
AUTH0_AUDIENCE=https://your-api
AUTH0_ISSUER=https://nextgen-scheduler.eu.auth0.com/
AUTH0_CLIENT_ID=...
AUTH0_CLIENT_SECRET=...
AUTH_METHODS=sso,passwordless,mfa
CORS_ORIGINS=http://localhost:3000
ENV=development
DEBUG=true
RATE_LIMIT=100/minute
```

### Run backend

```bash
uvicorn backend.api.main:app --reload
```

### Main backend routes

- `GET /` health check
- `POST /auth/token` user credential token
- `GET /auth/sso/start?redirect_to=/dashboard`
- `GET /auth/sso/callback?code=x&state=y`
- `POST /auth/passwordless/request`
- `POST /auth/passwordless/verify`
- `POST /auth/mfa/setup`
- `POST /auth/mfa/verify`
- `GET /auth/check` token existence + payload check
- `GET /access-control/check-role` and `/check-attribute`

### Auth0 Integration flow

1. `AUTH0_DOMAIN` and `AUTH0_AUDIENCE` required for Auth0 mode.
2. `auth/schemes.py` obtains JWKs from `https://{AUTH0_DOMAIN}/.well-known/jwks.json`.
3. Validates RS256 token, audience, issuer.
4. Fallback: traditional stateful `SECRET_KEY` HS256.

---

## Frontend

### Frontend setup

```bash
cd frontend
npm install
```

Add configuration in `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Start frontend

```bash
npm run dev
```

### Pages

- `/` landing page
- `/auth/login` login
- `/auth/sso` SSO redirect with `?next=/dashboard`
- `/auth/mfa` MFA verify
- `/auth-callback` callback handling and redirect
- `/dashboard` protected page

### Guards

- `middleware.ts` guards `/dashboard/:path*` (requires cookie `graftai_access_token`)
- `AuthProvider` in `layout.tsx` checks `/auth/check` and refreshes every 45s

### API utility

`frontend/src/lib/api.ts` exposes:
- `login()`, `verifyToken()`
- `passwordlessRequest()`, `passwordlessVerify()`
- `mfaVerify()`
- `doitAuthCheck()`, `refreshSession()`

`frontend/src/lib/auth.ts` exposes:
- `getToken()`, `setToken()`, `clearToken()`
- `decodeJwtPayload()`, `isTokenExpired()`, `ensureTokenValid()`

---

## Running the App

1. Start backend:
   - `cd backend && uvicorn backend.api.main:app --reload`
2. Start frontend:
   - `cd frontend && npm run dev`
3. Open `http://localhost:3000`
4. Log in via `/auth/login` or `/auth/sso?next=/dashboard`

---

## Testing

### Lint and build

```bash
cd frontend
npm run lint
npm run build
```

### Backend tests

Add tests to `backend/tests` using `pytest` and run:

```bash
cd backend
pytest
```

---

## Deployment

### Docker (recommended local / cloud container host)

1. Create `backend/.env` and `frontend/.env.production` with production secrets:
   - `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `AUTH0_*`, `CORS_ORIGINS`, etc.
2. Build and run:
   - `docker compose build`
   - `docker compose up -d`
3. Verify:
   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:3000`

### Vercel (frontend only; backend should be a separate service / managed API)

- `vercel.yml` and `.vercelignore` are added for monorepo setup.
- Set these env vars in Vercel project settings:
  - `NEXT_PUBLIC_API_BASE_URL`, `API_BASE_URL`, `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, etc.
- Ensure a separate deployment host (e.g., AWS ECS/GCP Cloud Run/DigitalOcean App) for `backend`.

### GitHub

- `.gitignore` now includes Docker artifacts, Vercel config, and environment files.
- Use GitHub Actions with build & test check before merge; example workflow can be added in `.github/workflows/`.

### Production hardening

- `CORS_ORIGINS` should be set to your real domain (https://yourdomain.com)
- `ENV=production`, `DEBUG=false`
- `SECRET_KEY`, `JWT_SECRET`, `DATABASE_URL`, `SENTRY_DSN` (opt.) must be managed secrets
- Confirm HTTPS with TLS terminated at CDN/load balancer
- Enable periodic dependency audit and security scanning.

### Render-specific backend deployment

- Set `Start Command:`
  - `cd backend && uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT --workers 4 --proxy-headers`
  - alternative: `cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.api.main:app --bind 0.0.0.0:$PORT`
- Environment variables:
  - `PYTHONPATH=/opt/render/project/src/backend` if Render is using repository root as workdir
  - `CORS_ORIGINS=https://yourfrontend.com`
  - `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `JWT_SECRET`, `ENV=production`, `DEBUG=false`
- Add fallback entrypoint in root: `app.py` (already provided) so this is compatible with `uvicorn app:app`.

---

## Troubleshooting

- `auth/sso/callback` returns missing code: ensure provider callback URL matches `OAUTH2_REDIRECT_URI`.
- Build errors (Next.js): check `middleware.ts` matcher and client component Guard.
- Token expired: clear browser storage + re-login.

---

## Contribution

1. Fork repo.
2. Create feature branch (`feature/<name>`).
3. Code, lint, and test.
4. Create PR.

---

## Licensing

TBD (add MIT/Apache etc as required)
