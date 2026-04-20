# Technical Document

## Overview
This technical document captures the main implementation details of GraftAI, including frontend and backend design, API contract patterns, real-time features, and engineering assumptions.

## Frontend Architecture
- **Framework**: Next.js App Router, React 19, TypeScript.
- **Client features**:
  - dashboard and public booking interfaces
  - booking flows, pricing pages, settings, and team management
  - service worker caching via `frontend/public/sw.js`
  - offline-aware API client with retry and queue support in `frontend/src/lib/api-client-enhanced.ts`

## Backend Architecture
- **Framework**: FastAPI with async endpoints.
- **Data persistence**: PostgreSQL / SQLAlchemy.
- **Queue / cache**: Redis for realtime sync and background jobs.
- **Authentication**: JWT and OAuth flows handled in `backend/auth` and session middleware.

## Core API Surfaces
- `/api/auth/*` for login, logout, restore, and provider callbacks.
- `/api/events/upcoming` for calendar event feeds.
- `/api/plugins` for plugin discovery and execution.
- `/api/proactive` for AI-driven workflows and suggestions.
- `/api/user/preferences` for user profile and settings.

## Service Worker and Offline Support
- `frontend/public/sw.js` bundles a precache manifest and runtime caching strategies.
- Static assets and route fragments are cached to improve load performance and offline behavior.
- The service worker currently bypasses `/api/` requests to preserve live backend behavior.

## Data Model
- Core entities include users, bookings, events, teams, and plugin metadata.
- `backend/models/tables.py` defines primary tables and relationships.
- Uploads are abstracted through `backend/services/storage.py` with support for S3/R2 and local fallback.

## Security and Validation
- JWT payloads are validated with versioning and expiry checks.
- API routes enforce authentication where required.
- Environment secrets are read from `.env` files locally and injected securely in production.

## Observability
- Telemetry endpoints and health checks are exposed for runtime diagnostics.
- Real-time analytics and monitoring are surfaced through the dashboard UI.

## Build and Tooling
- Frontend build: `npm run build` with `postbuild` sanitizer.
- Backend build: Python packaging with `requirements.txt` and `pyproject.toml` for backend-specific code.
- Linters and formatters should be configured for TypeScript and Python.

## Engineering Decisions
- Use `serwist` service worker tooling for predictable caching.
- Keep AI and real-time behavior modular to isolate external provider integration.
- Maintain separate frontend and backend deployments for scalability.

## Known Gaps
- Some endpoints still allow `any` type warnings in TypeScript and require stricter typing.
- The service worker manifest is generated at build time and needs the sanitizer step to normalize Windows path artifacts.
- Advanced quota behavior is managed in `backend/utils/quota_middleware.py` and should be audited before production.
