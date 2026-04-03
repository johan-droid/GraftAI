# 🔐 GraftAI Authentication System - Reconstruction Plan

## 🚨 Critical Issue Identified

**Error**: `GET /api/auth/sign-in/social` returns **500 Internal Server Error**

**Root Cause**: Better Auth initialization is failing due to:
1. Missing or invalid database connection
2. Missing `BETTER_AUTH_SECRET` environment variable
3. Social provider configuration errors
4. Database tables may not exist or schema mismatch

---

## ✅ TODO Plan - Complete Auth System Reconstruction

### Phase 1: Environment Configuration (IMMEDIATE) ✅ COMPLETED

- [x] Create `.env.local` file in frontend with required variables
- [ ] Create `.env` file in backend with required variables
- [x] Set `BETTER_AUTH_SECRET` placeholder (minimum 32 characters)
- [x] Configure `DATABASE_URL` for Better Auth
- [x] Set `NEXT_PUBLIC_APP_URL` correctly

### Phase 2: Database Schema Verification ✅ COMPLETED

- [x] Verify `users`, `session`, `account` tables exist
- [x] Ensure column names match Better Auth expectations
- [x] Created migration script `backend/scripts/auth_schema.sql`

### Phase 3: Better Auth Configuration Fix ✅ COMPLETED

- [x] Fixed auth-server.ts with proper error handling
- [x] Added connection validation before auth init
- [x] Handle missing DB gracefully with clear errors
- [x] Fixed social provider configuration
- [x] Added `getAuthStatus()` export for diagnostics

### Phase 4: Route Handler Improvements ✅ COMPLETED

- [x] Add detailed error logging in `[...auth]/route.ts` (already present)
- [x] Return structured error responses (already present)
- [x] Updated `/api/auth-diagnostic` endpoint with comprehensive status

### Phase 5: Testing & Validation ⏳ PENDING

- [ ] Test `/api/auth-diagnostic` endpoint
- [ ] Test `/api/auth/providers` endpoint
- [ ] Test social sign-in flow
- [ ] Test credential sign-in flow

---

## 📋 Required Environment Variables

### Frontend (.env.local) ✅ CREATED

```bash
# Required
NODE_ENV=development
NEXT_PUBLIC_APP_URL=http://localhost:3000
BETTER_AUTH_SECRET=dev-secret-key-change-in-production-min-32-chars
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/graftai

# Optional - Social Providers
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
```

### Backend (.env) ⏳ TODO

```bash
# Required
SECRET_KEY=your-backend-secret-key-minimum-32-characters
DATABASE_URL=postgresql://user:password@localhost:5432/graftai

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 🗄️ Database Schema Requirements

### users table
```sql
- id (VARCHAR, PRIMARY KEY)
- email (VARCHAR, UNIQUE, NOT NULL)
- full_name (VARCHAR)
- hashed_password (VARCHAR)
- emailVerified (BOOLEAN)
- createdAt (TIMESTAMP)
- updatedAt (TIMESTAMP)
```

### session table
```sql
- id (VARCHAR, PRIMARY KEY)
- userId (VARCHAR, FOREIGN KEY -> users.id)
- expiresAt (TIMESTAMP)
- createdAt (TIMESTAMP)
- updatedAt (TIMESTAMP)
- ipAddress (VARCHAR)
- userAgent (TEXT)
```

### account table
```sql
- id (VARCHAR, PRIMARY KEY)
- userId (VARCHAR, FOREIGN KEY -> users.id)
- accountId (VARCHAR)
- providerId (VARCHAR)
- accessToken (TEXT)
- refreshToken (TEXT)
- accessTokenExpiresAt (TIMESTAMP)
- createdAt (TIMESTAMP)
- updatedAt (TIMESTAMP)
```

---

## 🔧 Implementation Steps

### Step 1: Create Environment Files
Create `.env.local` in frontend directory with all required variables.

### Step 2: Fix auth-server.ts
Add proper error handling and validation for database connection.

### Step 3: Update route handlers
Add better error logging and structured responses.

### Step 4: Create migration script
Ensure database tables exist with correct schema.

### Step 5: Test endpoints
Verify all auth endpoints work correctly.

---

## 📊 Expected Endpoint Behavior

### GET /api/auth-diagnostic
```json
{
  "environment": "development",
  "hasDatabase": true,
  "hasBetterAuthSecret": true,
  "betterAuthUrl": "http://localhost:3000",
  "databaseType": "PostgreSQL",
  "dbConnectionStatus": "connected"
}
```

### GET /api/auth/providers
```json
{
  "providers": ["google", "github"],
  "env": "development"
}
```

### POST /api/auth/sign-in/social
**Success**: Redirect to provider OAuth URL
**Error**: 
```json
{
  "error": "provider_not_configured",
  "message": "Google OAuth is not configured",
  "status": 400
}
```

---

## 🚀 Quick Start Commands

```bash
# 1. Install dependencies
cd frontend && npm install

# 2. Create .env.local
cp .env.example .env.local
# Edit .env.local with your values

# 3. Run database migrations
# (Use your preferred migration tool)

# 4. Start development server
npm run dev

# 5. Test diagnostic endpoint
curl http://localhost:3000/api/auth-diagnostic
```

---

## 🐛 Common Issues & Solutions

### Issue: 500 Error on /api/auth/sign-in/social
**Solution**: Check BETTER_AUTH_SECRET is set and database is connected

### Issue: Database connection failed
**Solution**: Verify DATABASE_URL format and PostgreSQL is running

### Issue: No social providers available
**Solution**: Configure at least one OAuth provider or use email/password

### Issue: Session not persisting
**Solution**: Check cookie settings and SameSite configuration

---

## 📝 Notes

- Better Auth uses opaque tokens stored in database sessions
- Legacy JWT fallback is maintained for API compatibility
- All auth routes are under `/api/auth/*`
- CSRF protection is enabled by default in Better Auth
- Rate limiting should be configured per endpoint

---

**Last Updated**: $(date)
**Status**: IN PROGRESS
