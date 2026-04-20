# SES Documentation

## 1. Purpose
This Software Engineering Specification (SES) defines the architecture, requirements, and operational behavior of the GraftAI application. It is intended for engineers, architects, reviewers, and operations teams to align implementation, testing, and deployment.

## 2. Scope
GraftAI provides a unified scheduling, booking, and intelligence platform with:
- authenticated user dashboards
- public booking pages
- calendar integration with external providers
- AI-assisted workflow recommendations
- real-time telemetry and quota enforcement
- extensible plugin architecture

## 3. Functional Requirements
- User authentication and authorization using OAuth2 / JWT.
- Booking creation, rescheduling, and cancellation workflows.
- Calendar synchronization with Google and Apple provider connectors.
- Usage quotas and billing plan enforcement for each team or account.
- Realtime dashboards for analytics and AI recommendations.
- Service worker support for offline-first route handling and caching.

## 4. Architecture Overview
GraftAI uses a dual-tier architecture:
- **Frontend**: Next.js App Router with React 19, TypeScript, and Tailwind-like responsive styling.
- **Backend**: FastAPI with async SQLAlchemy, PostgreSQL, Redis, and background workers.
- **Services**: OAuth, token management, calendar provider proxy, analytics, and quota enforcement.

### 4.1 System Components
- **Authentication**: NextAuth integrated with FastAPI and JWT session validation.
- **API Layer**: `/api/*` endpoints serving auth, analytics, booking, plugin, and proactive features.
- **Data Layer**: PostgreSQL for core entities plus Redis for real-time state and queueing.
- **Offline Caching**: `frontend/public/sw.js` precaches static assets and handles runtime fetch strategies.

## 5. Quality Attributes
- **Reliability**: Safe default API error handling, retry paths, and offline cache fallback.
- **Security**: Scoped JWT validation, HMAC verification for webhooks, environment-secret isolation.
- **Performance**: Static pre-rendering for public pages, caching in service worker, and async backend tasks.
- **Scalability**: Separate compute for backend, Redis, and storage services.

## 6. Deployment and Release
- Backend deploys via containerized FastAPI service.
- Frontend deploys via Next.js build output and service worker assets.
- CI/CD should run lint and build for both packages, then publish from `main`.

## 7. Compliance Notes
- Secrets must remain out of source control.
- `.env*` files are ignored and should never be committed.
- Production configuration should use environment-managed credentials only.

## 8. Risk Register
- Calendar provider token refresh failure.
- Rate limiting on third-party AI providers.
- Insecure storage of local file uploads.
- Service worker cache mismatch after frontend asset changes.

## 9. References
- `docs/DEVELOPER_GUIDE.md`
- `docs/FRONTEND_DOCUMENTATION.md`
- `frontend/public/sw.js`
- `backend/services/storage.py`
