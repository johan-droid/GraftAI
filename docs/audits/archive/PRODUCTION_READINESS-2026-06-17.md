# GraftAI Production Readiness & Refactoring Instructions

## Agent Mission
You are tasked with refactoring the **GraftAI** codebase to transition it from a prototype to a production-ready SaaS platform. The current codebase suffers from critical race conditions, security vulnerabilities, caching anti-patterns, and scalability bottlenecks. 

Execute the following fixes systematically. Ensure all changes maintain backward compatibility with the frontend (Next.js 19) and do not break existing integration tests.

---

## Phase 1: Critical Race Conditions & Data Consistency

### 1.1 Quota & Rate Limit Race Conditions
**The Issue:** The system currently uses a "Read-Modify-Write" pattern in PostgreSQL for quota deduction. Under concurrent load, this leads to quota exploitation and bypassed limits.
**The Fix:** Move all quota and rate-limiting logic to Redis using Atomic Lua Scripts.
**Implementation:**
- Locate quota deduction logic in the backend services.
- Replace DB-based deduction with a Redis Lua script:
```python
# backend/services/quota_service.py (or relevant file)
LUA_QUOTA_DEDUCT = """
local current = redis.call('GET', KEYS[1])
if tonumber(current) > 0 then
    return redis.call('DECR', KEYS[1])
end
return -1
"""
async def deduct_quota(user_id: str, redis_client):
    key = f"quota:{user_id}"
    result = await redis_client.eval(LUA_QUOTA_DEDUCT, 1, key)
    if result == -1:
        raise HTTPException(status_code=429, detail="Quota exceeded")
    return result
```

### 1.2 Calendar Sync Collisions
**The Issue:** Multiple webhooks or cron jobs triggering syncs simultaneously for the same user corrupt the local database state (`concurrent_syncs > 1`).
**The Fix:** Implement Redis Distributed Locks (Redlock) keyed by `user_id` before initiating any sync task.
**Implementation:**
- In your Celery/arq tasks or background sync handlers:
```python
async def perform_calendar_sync(user_id: str, redis_client):
    lock_key = f"calendar_sync_lock:{user_id}"
    # Use a blocking lock with a timeout to prevent deadlocks
    async with redis_client.lock(lock_key, timeout=60, blocking_timeout=5):
        await execute_sync_logic(user_id)
```

### 1.3 Booking Transaction Conflicts & Orphaned Records
**The Issue:** High load causes `duplicate_bookings`. Orphaned records occur due to missing cascade rules.
**The Fix:** 
1. **Idempotency:** Require an `Idempotency-Key` header for all `POST /bookings` requests.
2. **DB Constraints:** Enforce `ON DELETE CASCADE` for foreign keys. Add a `UNIQUE` constraint on `(user_id, slot_start, slot_end)` in the `bookings` table.
3. **Isolation:** Use `SERIALIZABLE` or `REPEATABLE READ` for booking transactions in SQLAlchemy.

---

## Phase 2: Security & Input Sanitization

### 2.1 Hardcoded Secrets & Environment Chaos
**The Issue:** The code explicitly checks for/uses default secrets like `super-secret-college-project-key-change-in-prod`. 
**The Fix:** 
- Create a strict `Pydantic BaseSettings` class for configuration validation.
- **Hard Fail on Startup:** In the FastAPI `lifespan` event, if `ENV=production` and `SECRET_KEY` is the default string, raise a `RuntimeError` and refuse to boot.
```python
# backend/core/config.py
class Settings(BaseSettings):
    secret_key: str
    env: str = "development"

    @model_validator(mode='after')
    def validate_production_secrets(self):
        if self.env == "production" and self.secret_key == "super-secret-college-project-key-change-in-prod":
            raise ValueError("CRITICAL: Default secret key used in production!")
        return self
```

### 2.2 XSS & SQL Injection
**The Issue:** Potential unsanitized inputs in AI prompts and calendar descriptions.
**The Fix:**
- **Backend:** Ensure *zero* raw SQL string concatenation. Use `bleach` for any user-generated content stored in the DB.
- **Frontend:** The `MarkdownRenderer` in `frontend/components/AIChat/MarkdownRenderer.tsx` uses `rehypeSanitize`. Ensure this is strictly applied to all AI outputs. Never use `dangerouslySetInnerHTML` without it.

### 2.3 Secure File Uploads
**The Issue:** Avatar/Attachment uploads need strict containment.
**The Fix:**
- Ensure all uploaded files are renamed to a UUID.
- When serving via proxy/S3, force headers: `Content-Disposition: attachment` and `Content-Type: application/octet-stream`.

---

## Phase 3: Architecture & Technical Debt

### 3.1 AI Service Hardcoding & Fallbacks
**The Issue:** Direct Groq/OpenAI integration in `backend/ai/llm_core.py` without abstraction or fallback strategy.
**The Fix:** Implement the Strategy Pattern or integrate `LiteLLM`. Add Circuit Breaker logic.
```python
# backend/ai/llm_core.py refactoring
class LLMProvider(Protocol):
    async def complete(self, messages: list[dict]) -> str: ...

class LLMRouter:
    def __init__(self, primary: LLMProvider, fallback: LLMProvider):
        self.primary = primary
        self.fallback = fallback
        self._circuit_open = False

    async def complete(self, messages: list[dict]) -> str:
        if self._circuit_open:
            return await self.fallback.complete(messages)
        try:
            return await self.primary.complete(messages)
        except Exception:
            self._circuit_open = True
            return await self.fallback.complete(messages)
```

### 3.2 Caching System & Cache Stampede
**The Issue:** Mixed Redis and in-memory caching without invalidation strategy.
**The Fix:** 
- Remove local `dict` or `lru_cache` for shared state.
- Implement the **Cache-Aside pattern** with a logical expiration. Use Redis `SETNX` to create a mutex lock for cache regeneration to prevent stampedes.

### 3.3 Database Connection Pool Exhaustion
**The Issue:** Bottleneck at 100 connections.
**The Fix:** 
- Ensure all DB sessions are properly closed using FastAPI `Depends(get_db)` with `async with` context managers.
- Recommend deploying **PgBouncer** in the infrastructure layer.

---

## Phase 4: Production Resilience & Error Handling

### 4.1 Redis Dependency & Graceful Degradation
**The Issue:** If Redis goes down, critical quota paths return `503 Service Unavailable`.
**The Fix:** Implement a **Local Token Bucket Fallback**. If Redis is unreachable, fallback to an in-memory rate limiter for the specific pod, log a critical alert, and allow the request to proceed (or fail gracefully without a 503).

### 4.2 Standardized Error Handling
**The Issue:** Mixed `HTTPException` and custom errors leaking stack traces.
**The Fix:** Add a global exception handler in FastAPI.
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log to Sentry
    logger.exception("Unhandled error", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "request_id": request.headers.get("X-Request-ID")},
    )
```

### 4.3 Payment Webhook Security
**The Issue:** `RAZORPAY_WEBHOOK_SECRET not set` warning.
**The Fix:** Webhook signature verification is **mandatory**. If the secret is missing in production, the endpoint must reject all requests with a 500 error. Implement Stripe/Razorpay signature validation middleware.

---

## Phase 5: Testing & CI/CD Infrastructure

### 5.1 Mandatory Test Coverage
- Enforce `pytest-cov` with a minimum threshold of 80% in the CI pipeline.
- Write `pytest-asyncio` integration tests using `httpx.AsyncClient` and `testcontainers` for PostgreSQL/Redis.

### 5.2 Pre-Commit Hooks
- Ensure `.pre-commit-config.yaml` enforces `detect-secrets`, `ruff`, and `eslint` locally and in CI.

---

## 🚀 Execution Strategy (Agent Action Plan)

Execute the fixes in the following order to ensure stability:

1. **Stop the Bleeding (Security):** 
   - Add the `SECRET_KEY` validation check to the FastAPI `lifespan` event.
   - Enforce webhook signature validation.
2. **Fix the Data Corruptors (Race Conditions):**
   - Refactor Quota deduction to use Redis Lua scripts.
   - Add Redis Distributed Locks to the Calendar Sync tasks.
   - Add `UNIQUE` constraints to booking slots via Alembic migration.
3. **Refactor AI & Caching:**
   - Abstract `LLaMACore` to use the Strategy/Router pattern.
   - Fix cache stampede vulnerabilities in Redis caching logic.
4. **Error Handling & Resilience:**
   - Implement the global exception handler.
   - Add the local fallback for Redis rate limiting.

### Agent Constraints:
- **Do not** alter the frontend component interfaces (`AgentExecutionTimeline`, `MarketingShell`, etc.) unless strictly necessary for error state handling.
- **Do not** remove existing Prometheus metrics (`agent_executions`, `tool_duration`, etc.); ensure your refactored code still calls them.
- Ensure all new async functions properly handle `asyncio.TimeoutError` and translate them to user-friendly messages.
