# GraftAI — Agent Protocol & Engineering Standards

## Project Identity

GraftAI is an AI-powered scheduling platform (SaaS) competing with Calendly and Cal.com. It provides automated booking, calendar sync, AI copilot, workflow automation, and multi-provider OAuth — all wrapped in a premium "Material You" aesthetic.

---

## Architecture

```
GraftAI/
├── backend/          # FastAPI (Python 3.12+) — API server, Celery workers
│   ├── api/          # Route handlers (bookings, billing, auth, calendar, AI chat, webhooks, etc.)
│   ├── auth/         # JWT config, OAuth schemes, security middleware
│   ├── core/         # Redis client, Celery app, settings
│   ├── models/       # SQLAlchemy ORM tables (UserTable, BookingTable, EventTypeTable, etc.)
│   ├── services/     # Business logic (bookings, scheduler, booking_automation, workflow_engine, etc.)
│   ├── tasks/        # Celery background tasks (automation, reminders)
│   ├── utils/        # Rate limiting, caching, error classes, GDPR compliance
│   ├── ai/           # LLM orchestration, fallback chain, soft prompt engine
│   ├── alembic/      # Database migrations
│   └── Dockerfile    # Multi-stage UV build, non-root user, healthcheck
├── frontend/         # Next.js 16 (App Router) — TypeScript, Tailwind CSS 4
│   ├── src/app/      # Route segments (dashboard, auth, public booking, embed, etc.)
│   ├── src/lib/      # API client (retry+backoff), auth helpers, theme tokens
│   ├── src/hooks/    # React hooks (useQuery, useCalendar, useNetworkStatus, etc.)
│   ├── src/components/ # UI components
│   └── middleware.ts # CSP nonce injection, route protection
├── docker-compose.yml # 3 backend replicas + Nginx LB + Postgres + Redis
├── render.yaml       # Render deployment (API + Celery worker + Postgres)
└── nginx/            # Load balancer config
```

### Key Technology Decisions

| Layer | Stack | Version |
|-------|-------|---------|
| Backend runtime | Python | ≥3.12 |
| Backend framework | FastAPI + Pydantic v2 | ≥0.110 |
| Database ORM | SQLAlchemy 2 (async) + Alembic | ≥2.0 |
| Database | PostgreSQL (Neon, asyncpg) / SQLite (dev) | 15+ |
| Cache & Pub/Sub | Redis (Upstash) | ≥5.0 |
| Task queue | Celery (Redis broker) | — |
| Auth backend | python-jose JWT + Argon2 | — |
| Frontend framework | Next.js (App Router) | 16 |
| Frontend auth | Auth.js / NextAuth v5 (beta) | ≥5.0-beta |
| Styling | Tailwind CSS 4 + Emotion + MUI 6 | — |
| State management | TanStack Query v5 | ≥5.0 |
| PWA / Offline | Serwist (service worker) | ≥9.5 |
| AI / LLM | Groq (Llama 3.3-70B), OpenAI, LangChain | — |
| Vector DB | Pinecone | ≥5.0 |
| Payments | Stripe + Razorpay (dual-gateway) | — |
| Monitoring | Sentry (opt-in) | — |
| Deployment | Render (web + worker) / Docker Compose | — |

---

## Critical Conventions — MUST Follow

### 1. Database & Transactions

- **Always use async sessions** via `get_db()` dependency injection.
- **Booking creation requires atomic transactions** with `SERIALIZABLE` isolation and `WITH FOR UPDATE` row locks to prevent double-booking.
- **Soft-delete pattern**: Models use `is_deleted` flag; never hard-delete user-facing records.
- **Migrations**: All schema changes go through Alembic. Never modify tables directly.
- **Connection pooling**: Production uses `pool_size=5`, `max_overflow=10`, `pool_recycle=1800`. Do not change without load testing.

### 2. Authentication & Security

- **Dual-token architecture**: NextAuth (frontend session) issues a `backendToken` by calling `POST /api/v1/auth/social/exchange`. Backend issues its own JWT pair (access + refresh).
- **JWT secret enforcement**: Production startup rejects secrets shorter than 256 bits or matching known defaults. See `backend/auth/config.py`.
- **Token rotation**: Refresh tokens are single-use — the old token is blacklisted in Redis upon refresh.
- **Token version**: `user.token_version` enables instant mass-revocation. Bumping it invalidates all existing tokens for that user.
- **Cookie security**: In production/Render, cookies are `Secure; HttpOnly; SameSite=None`.
- **Rate limiting**: Redis sliding-window per-endpoint. Auth endpoints: 5 req/min. AI chat: 60 req/min.
- **NEVER** commit `.env` files. All secrets go in Render Dashboard (or platform-specific secret manager).

### 3. API Patterns

- All API routes live under `backend/api/` and are registered via `APIRouter` with prefix and tags.
- **Error responses** use FastAPI's `HTTPException` with explicit status codes.
- **Input validation** uses Pydantic `BaseModel` with `ConfigDict(extra='forbid')` and `@field_validator` for sanitization (HTML escaping, timezone enforcement).
- **Idempotency**: Booking creation supports `X-Idempotency-Key` header to prevent duplicate submissions.
- **Background work**: Use Celery tasks (`backend/tasks/`), NOT `asyncio.create_task()`. Celery survives worker restarts and supports retry/DLQ.
- **When passing Pydantic models to Celery**: Always call `.model_dump()` first — Celery's JSON serializer cannot handle BaseModel instances.

### 4. Frontend Patterns

- **API calls**: Use the singleton `apiClient` from `src/lib/api-client.ts`. It handles auth headers, retry with exponential backoff (3 retries), 401 auto-signout, and structured error parsing.
- **Server components** are the default. Use `'use client'` only when React hooks or browser APIs are needed.
- **Auth state**: Access via `useSession()` (client) or `auth()` (server). The `backendToken` is attached to the session object.
- **CSP**: `middleware.ts` injects a per-request nonce for inline scripts. Never use `unsafe-inline`.
- **Styling priority**: Tailwind CSS 4 utilities first, Emotion/MUI for complex components.

### 5. AI & Automation

- **Booking automation** uses a 3-level fallback chain: AI Agent → Rule-based engine → Manual review queue.
- **LLM provider**: Groq (Llama 3.3-70B) is the primary provider. OpenAI is the fallback. See `backend/ai/fallback.py`.
- **AI Orchestra**: Managed by `AgentController` in `backend/ai/orchestrator.py`. Features 4 specialized agent types:
    - `BookingAgent`: Handles scheduling logic and slot discovery.
    - `OptimizationAgent`: Refines calendar efficiency.
    - `ExecutionAgent`: Performs tool-based actions (sending emails, updating CRM).
    - `MonitoringAgent`: Tracks workflow health and logs metrics.
- **Memory Layer**: Uses a multi-layer system with `VectorStore` (Pinecone) for long-term retrieval and `GraphStore` for relationship mapping.
- **AI quota**: Users have daily AI message limits based on tier (free=10, pro=200, elite=2000). Enforced in `backend/services/ai_quota.py`.

### 6. SaaS Metering & Usage

- **Global Usage Service**: `backend/services/usage.py` is the source of truth for all meter readings.
- **Metrics Tracked**:
    - `daily_ai_count`: Messages sent to AI copilot (resets daily).
    - `total_ai_tokens`: Cumulative tokens consumed via LLM.
    - `total_api_calls`: External API requests made by agents/integrations.
    - `total_scheduling_count`: Lifetime bookings managed by the platform.
- **Audit Endpoint**: `GET /api/v1/audit/stats` serves these metrics to the frontend Sidebar.
- **Increment Pattern**: Always call `increment_usage(db, user_id, "metric_name", count)` within the service layer.

### 7. Background Tasks (Celery)

All async work MUST use the following task registry:
- `automation_tasks.py`: AI workflow execution and agent dispatch.
- `calendar_tasks.py`: OAuth sync and webhook processing.
- `email_tasks.py`: Notifications and transactional mail.
- `reminder_tasks.py`: SMS/Email event reminders.
- `webhook_tasks.py`: Outbound integration triggers.

### 8. Code Quality

- **Python linting**: `ruff` (configured in pyproject.toml).
- **TypeScript**: Strict mode. The build must pass `next build` with zero type errors.
- **No `print()` in production code** — use `logging.getLogger(__name__)` or `backend/utils/logger.py`.
- **No `datetime.utcnow()`** — it's deprecated in Python 3.12. Use `datetime.now(timezone.utc)` instead.
- **No `TODO`/`FIXME` in shipping code** without a linked issue tracker reference.

---

## Known Technical Debt

| ID | Issue | File | Status |
|----|-------|------|--------|
| TD-1 | `date_parser.parse()` called on already-validated `datetime` (TypeError) | `backend/api/bookings.py` | ✅ Fixed |
| TD-2 | `attendee_data` referenced before assignment (NameError) | `backend/api/bookings.py` | ✅ Fixed |
| TD-3 | Celery `.delay()` receives Pydantic BaseModel (EncodeError) | `backend/api/bookings.py` | ✅ Fixed |
| TD-4 | 50+ `datetime.utcnow()` calls across services (Deprecated) | Multiple files | ✅ Fixed |
| TD-5 | **BROKEN IMPORT**: `get_usage_counts` missing from `usage.py` | `ai_quota.py` | ✅ Fixed |
| TD-6 | 13+ Ghost frontend API endpoints with no backend | `frontend/src/lib/api.ts` | ✅ Fixed (Commented) |
| TD-7 | Hardcoded meter bar widths in Sidebar | `Sidebar.tsx` | ✅ Fixed (Dynamic) |
| TD-8 | LLM Model IDs stale (Groq 3.1 vs 3.3) | `llm_core.py` | ✅ Fixed |
| TD-9 | Process-memory conversation history (Not production-safe) | `llm_core.py` | ⚠️ Pending (Redis) |

---

## Deployment

### Render (Production)
- **API**: `render.yaml` → `graftai-api` web service (Uvicorn, proxy-headers).
- **Worker**: `render.yaml` → `graftai-celery-worker` (dedicated Celery process).
- **Database**: Managed Postgres via Render (`graftai-db`).
- **Redis**: External (Upstash). Must be provisioned manually.
- **Secrets**: All sensitive values use `sync: false` in render.yaml — set manually in Render Dashboard.

### Docker Compose (Staging/Local)
- 3 backend replicas behind Nginx load balancer.
- Local Postgres 15 + Redis 7.
- `docker-compose.yml` at project root.

### Environment Variables (Required)
```
DATABASE_URL          # asyncpg connection string
REDIS_URL             # Redis connection (rediss:// for TLS)
SECRET_KEY            # ≥256-bit hex, used for JWT signing
NEXTAUTH_SECRET       # ≥256-bit hex, used by Auth.js
GOOGLE_CLIENT_ID      # OAuth
GOOGLE_CLIENT_SECRET  # OAuth
FRONTEND_URL          # e.g. https://www.graftai.tech
BACKEND_URL           # e.g. https://graftai-abu1.onrender.com
```

---

## Agent Operating Principles

1. **Audit before implementing.** Understand the existing architecture and constraints before writing code.
2. **Harden before extending.** Fix bugs and close security gaps before adding features.
3. **Surgical edits only.** Use targeted diffs. Never rewrite entire files without justification.
4. **Preserve documentation.** Keep existing docstrings, comments, and architectural notes intact.
5. **Verify your work.** Run `ruff check`, `next build`, and relevant tests after changes.
6. **No secrets in code.** Never hardcode API keys, passwords, or tokens. Use environment variables.
