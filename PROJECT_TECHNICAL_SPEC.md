# 🌌 GraftAI: Technical Implementation Specification

## 1. Architectural Evolution
GraftAI has transitioned from a **Managed Neon Auth Proxy** to a **Standalone Better Auth** implementation. This architectural shift provides the following benefits:
- **Sovereignty**: Full control over session lifecycle and data persistence.
- **Direct Database Integration**: Zero-proxy connectivity to Neon Postgres via `pg.Pool`.
- **Simplified API**: Standard Next.js route handlers (`[...auth]`) replace custom proxy logic.

---

## 2. Authentication Engine (Standalone Better Auth)

### 2.1 Server-Side Auth (`frontend/src/lib/auth-server.ts`)
- **Core Strategy**: Uses `better-auth` with the standard `pg` pool adapter.
- **User Identity**: Mapped to the existing `users` table.
- **Integer ID Logic**: Configured to handle `INTEGER` primary keys for seamless integration with legacy user records.

### 2.2 Client-Side Auth (`frontend/src/lib/auth-client.ts`)
- **Compatibility Layer**: Exported helpers (`getSessionSafe`, `signInSocial`, `signUp`, `signOut`) ensure the existing UI components function without major refactors during the migration.
- **Provider**: Standard `better-auth/react` hooks (`useSession`) are available for new component development.

---

## 3. Database Schema & Mapping

The following tables have been manually applied to the Neon database to support Better Auth's session and account management:

### 3.1 `users` (Existing)
- **Primary Key**: `id` (INTEGER)
- **Identity Fields**: `email`, `name`, `image`.

### 3.2 `session` (New)
- Tracks active user sessions, tokens, and expiry.
- Linked to `users.id` via an integer foreign key.

### 3.3 `account` (New)
- Manages OAuth linked accounts (Google, GitHub) and credentials.
- Essential for cross-provider identification.

### 3.4 `verification` (New)
- Stores magic link tokens and email verification states.

---

## 4. Integration Context

### 4.1 Frontend API Routes
The standard Better Auth handler is mounted at:
`frontend/src/app/api/auth/[...auth]/route.ts`

### 4.2 Backend Synchronization
The backend (`backend/api/main.py`) expects a synchronized user record. The frontend initiates this via:
`POST /api/v1/auth/sync`

---

## 5. Development Workflow & Commands

### 5.1 Local Execution
Always run the orchestration command from the **project root** to ensure correct module resolution for both the FastAPI backend and Next.js frontend:

```powershell
npx concurrently -n "BACKEND,FRONTEND" "python -m uvicorn backend.api.main:app --reload --port 8000" "npm run dev --prefix frontend -- --port 3000"
```

### 5.2 Required Environment Variables
Ensure `frontend/.env.local` contains:
- `BETTER_AUTH_SECRET`: Minimum 32 characters.
- `DATABASE_URL`: Direct Postgres connection string.
- `GOOGLE_CLIENT_ID` / `SECRET`: Required for OAuth flows.

---

## 6. Implementation Status & Roadmap

| Feature | Status | Note |
| :--- | :--- | :--- |
| Standalone Auth Core | ✅ Done | Better Auth initialized and mapped to DB. |
| Schema Migration | ✅ Done | session, account, verification tables created. |
| Compatibility Helpers | ✅ Done | authClient helpers restored in frontend. |
| Google OAuth | ⏳ Pending | Awaiting user-provided Client ID/Secret. |
| E2E Flow Testing | ⏳ Pending | Awaiting full startup with valid credentials. |

---

## 7. Developer Notes
- **Route Collisions**: Any legacy `/api/auth/[...path]` routes must be removed to avoid conflicts with `[...auth]`.
- **SSL Handling**: The `pg.Pool` is configured with `rejectUnauthorized: false` for Neon compatibility.
- **Next.js Version**: The project is strictly optimized for Next.js 16+ using Turbopack.
