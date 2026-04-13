#!/usr/bin/env node
/**
 * GraftAI Auth Diagnostic Tool
 * Run: node scripts/auth-diag.js
 * 
 * Tests every step of the login flow and shows exactly where it breaks.
 */

const https = require("https");
const http  = require("http");

const BACKEND = "http://127.0.0.1:8000";
const API     = `${BACKEND}/api/v1`;

const RED    = "\x1b[31m";
const GREEN  = "\x1b[32m";
const YELLOW = "\x1b[33m";
const CYAN   = "\x1b[36m";
const RESET  = "\x1b[0m";
const BOLD   = "\x1b[1m";

function ok(label, msg)   { console.log(`${GREEN}  ✓${RESET} ${label}: ${msg}`); }
function fail(label, msg) { console.log(`${RED}  ✗${RESET} ${label}: ${RED}${msg}${RESET}`); }
function warn(label, msg) { console.log(`${YELLOW}  ⚠${RESET} ${label}: ${YELLOW}${msg}${RESET}`); }
function info(msg)        { console.log(`${CYAN}  ℹ${RESET} ${msg}`); }
function section(title)   { console.log(`\n${BOLD}${CYAN}═══ ${title} ═══${RESET}`); }

async function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith("https") ? https : http;
    const body = options.body || null;

    const req = lib.request(url, {
      method: options.method || "GET",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        ...(options.headers || {}),
      },
    }, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        let parsed;
        try { parsed = JSON.parse(data); } catch { parsed = data; }
        resolve({ status: res.statusCode, body: parsed, raw: data });
      });
    });
    req.on("error", reject);
    if (body) req.write(typeof body === "string" ? body : JSON.stringify(body));
    req.end();
  });
}

function parseJwt(token) {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(Buffer.from(b64, "base64").toString());
  } catch {
    return null;
  }
}

// ── env checks ────────────────────────────────────────────────────────────────
function checkEnv() {
  section("Environment Variables");

  const required = {
    BACKEND_URL: process.env.BACKEND_URL,
    NEXTAUTH_SECRET: process.env.NEXTAUTH_SECRET || process.env.AUTH_SECRET,
    GOOGLE_CLIENT_ID: process.env.GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET: process.env.GOOGLE_CLIENT_SECRET,
    MICROSOFT_CLIENT_ID: process.env.MICROSOFT_CLIENT_ID,
    MICROSOFT_CLIENT_SECRET: process.env.MICROSOFT_CLIENT_SECRET,
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  };

  let hasError = false;
  for (const [key, val] of Object.entries(required)) {
    if (!val) {
      fail(key, "NOT SET ← this will break auth!");
      hasError = true;
    } else {
      const masked = val.length > 8 ? val.slice(0, 4) + "****" + val.slice(-4) : "****";
      ok(key, masked);
    }
  }
  return !hasError;
}

// ── backend connectivity ──────────────────────────────────────────────────────
async function checkBackend() {
  section("Backend Connectivity");

  try {
    const r = await request(`${BACKEND}/health`);
    if (r.status === 200) ok("GET /health", `${r.status} OK`);
    else fail("GET /health", `${r.status} - ${JSON.stringify(r.body)}`);
  } catch (e) {
    fail("GET /health", `UNREACHABLE — ${e.message}`);
    return false;
  }

  try {
    const r = await request(`${API}/auth/check`, { headers: { Authorization: "Bearer invalid" } });
    if (r.status === 401) ok("GET /auth/check with bad token", "Correctly returns 401");
    else warn("GET /auth/check", `Unexpected status ${r.status}`);
  } catch (e) {
    fail("GET /auth/check", e.message);
  }

  return true;
}

// ── social exchange with a synthetic token ────────────────────────────────────
async function checkSocialExchange() {
  section("POST /auth/social/exchange (Token Format)");

  // Test with a clearly fake token to see the error shape
  const r = await request(`${API}/auth/social/exchange`, {
    method: "POST",
    body: {
      provider: "google",
      access_token: "fake_token_for_diag",
      email: "diag@test.com",
      name: "Diagnostic Test",
    },
  });

  if (r.status === 401) {
    ok("Endpoint reachable", `Status 401 as expected for fake token`);
    info(`Error detail: ${JSON.stringify(r.body)}`);
  } else if (r.status === 400) {
    ok("Endpoint reachable", `Status 400 - validation working`);
    info(`Detail: ${JSON.stringify(r.body)}`);
  } else if (r.status === 500) {
    fail("Server error", `500 — check backend logs. Body: ${JSON.stringify(r.body)}`);
  } else {
    warn("Unexpected status", `${r.status} — ${JSON.stringify(r.body)}`);
  }
}

// ── simulate the nextauth signIn callback ────────────────────────────────────
async function simulateSignInCallback() {
  section("Simulating NextAuth signIn Callback");

  info("This simulates exactly what auth.ts does when you click 'Continue with Google'");
  info("Backend URL that will be used: " + (process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000 [fallback]"));

  const backendUrl = (
    process.env.BACKEND_URL ||
    process.env.INTERNAL_BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");

  const url = `${backendUrl}/api/v1/auth/social/exchange`;
  info(`Will POST to: ${url}`);

  try {
    const r = await request(url, {
      method: "POST",
      body: {
        provider: "google",
        access_token: "REPLACE_WITH_REAL_TOKEN",
        email: "test@example.com",
        name: "Test User",
      },
    });

    if (r.status === 401) {
      ok("URL is correct", "Got 401 (expected for fake token) — endpoint reachable from Node.js context");
    } else if (r.status === 500) {
      fail("Backend error", `500 — this means signIn callback would return false! Body: ${r.raw}`);
    } else {
      info(`Status: ${r.status}, Body: ${JSON.stringify(r.body)}`);
    }
  } catch (e) {
    fail("FETCH FAILED", `${e.message} — This is why signIn returns false! Backend URL is wrong in server context.`);
    info("Fix: set BACKEND_URL=http://localhost:8000 in frontend/.env.local");
  }
}

// ── test a real JWT token pair (create one via /auth/refresh endpoint) ───────
async function checkJwtFlow() {
  section("JWT Token Validation");

  // We'll hit the refresh endpoint with a fake refresh token to see the error shape
  const r = await request(`${API}/auth/refresh`, {
    method: "POST",
    body: { refresh_token: "fake.refresh.token" },
  });

  if (r.status === 401) {
    ok("/auth/refresh", `Correctly rejects invalid refresh token (401)`);
    info(`Error: ${JSON.stringify(r.body)}`);
  } else if (r.status === 422) {
    warn("/auth/refresh", `Validation error — check request body format: ${JSON.stringify(r.body)}`);
  } else if (r.status === 500) {
    fail("/auth/refresh", `500 — backend crash! ${JSON.stringify(r.body)}`);
  } else {
    info(`Status: ${r.status}`);
  }
}

// ── check /users/me without token ────────────────────────────────────────────
async function checkUsersMe() {
  section("GET /users/me — Auth Validation");

  const r = await request(`${API}/users/me`);
  if (r.status === 401) {
    ok("/users/me without token", "Correctly requires auth (401)");
  } else if (r.status === 422) {
    warn("/users/me", `Unexpected 422 — ${JSON.stringify(r.body)}`);
  } else {
    fail("/users/me", `Unexpected ${r.status} — ${JSON.stringify(r.body)}`);
  }

  // Now try with a malformed bearer
  const r2 = await request(`${API}/users/me`, {
    headers: { Authorization: "Bearer malformed.jwt.token" },
  });
  if (r2.status === 401) {
    ok("/users/me with bad token", "Correctly rejects (401)");
  } else {
    warn("/users/me with bad token", `Got ${r2.status} — ${JSON.stringify(r2.body)}`);
  }
}

// ── next auth config check ───────────────────────────────────────────────────
function checkNextAuthConfig() {
  section("NextAuth Config Sanity Check");

  const secret = process.env.NEXTAUTH_SECRET || process.env.AUTH_SECRET;
  const backendSecret = process.env.SECRET_KEY;

  if (!secret) {
    fail("NEXTAUTH_SECRET", "Not set — sessions won't persist across restarts!");
  } else if (secret.length < 32) {
    warn("NEXTAUTH_SECRET", `Only ${secret.length} chars — should be at least 32`);
  } else {
    ok("NEXTAUTH_SECRET", `${secret.length} chars ✓`);
  }

  if (!backendSecret) {
    warn("Backend SECRET_KEY", "Not visible in frontend env — ensure backend/.env has SECRET_KEY set");
  } else {
    ok("Backend SECRET_KEY", `${backendSecret.length} chars`);
  }

  const googleId = process.env.GOOGLE_CLIENT_ID;
  if (googleId && !googleId.endsWith(".apps.googleusercontent.com")) {
    warn("GOOGLE_CLIENT_ID", "Doesn't end with .apps.googleusercontent.com — check the value");
  }

  const msId = process.env.MICROSOFT_CLIENT_ID;
  if (!msId) {
    fail("MICROSOFT_CLIENT_ID", "Not set in frontend/.env.local — Microsoft login will fail!");
  }
  const msTenant = process.env.MICROSOFT_TENANT_ID;
  if (!msTenant) {
    warn("MICROSOFT_TENANT_ID", "Not set — will default to 'common'");
  }
}

// ── check for routes that shadow NextAuth internal endpoints ────────────────
function checkRouteConflicts() {
  section("NextAuth Route Conflict Check");
  const fs   = require("fs");
  const path = require("path");
  const base = path.join(__dirname, "../frontend/src/app/api/auth");

  // NextAuth v5 RESERVES these paths — custom routes here WILL SHADOW them
  const reserved = ["signin", "signout", "session", "csrf", "providers"];
  let foundConflict = false;

  for (const name of reserved) {
    const routePath = path.join(base, name, "route.ts");
    const routePathJs = path.join(base, name, "route.js");
    if (fs.existsSync(routePath) || fs.existsSync(routePathJs)) {
      fail(`/api/auth/${name}`, `CONFLICT — your custom route.ts shadows NextAuth's internal handler!`);
      fail("Fix", `Delete frontend/src/app/api/auth/${name}/route.ts`);
      foundConflict = true;
    } else if (fs.existsSync(path.join(base, name))) {
      warn(`/api/auth/${name}`, "Directory exists but no route.ts — likely already removed");
    } else {
      ok(`/api/auth/${name}`, "No conflict");
    }
  }
  if (!foundConflict) ok("All reserved routes", "No conflicts detected");
}

function printSummary(results) {
  section("DIAGNOSIS SUMMARY");
  console.log(`
Common causes of "login then immediate logout":

${BOLD}1. signIn callback returns false${RESET} (most common)
   → Backend URL is wrong/unreachable from server-side Next.js
   → Fix: Ensure BACKEND_URL=http://localhost:8000 in frontend/.env.local

${BOLD}2. JWT callback stamps RefreshTokenError${RESET}
   → isBackendTokenExpired() triggers on first load
   → Fix: Applied in auth.ts — undefined expiry now treated as valid

${BOLD}3. AuthProvider signs out on first 401${RESET}  
   → /users/me returns 401 because deps.py used wrong SECRET_KEY
   → Fix: deps.py imports from auth/config.py

${BOLD}4. Two competing sessions${RESET}
   → Browser has stale cookies from a previous auth system
   → Fix: Clear all cookies for localhost:3000 and retry

${BOLD}To capture the exact failure:${RESET}
   Open http://localhost:3000/login in an incognito window
   Open DevTools → Network tab → filter "social/exchange"
   Click "Continue with Google" and watch the network request
   If social/exchange is NOT called → signIn callback URL is wrong
   If social/exchange returns non-200 → backend error
   If social/exchange returns 200 → check NextAuth jwt callback logs
`);
}

// ── main ──────────────────────────────────────────────────────────────────────
async function main() {
  console.log(`\n${BOLD}${CYAN}╔═══════════════════════════════════════════╗${RESET}`);
  console.log(`${BOLD}${CYAN}║   GraftAI Auth Diagnostic Tool v1.0       ║${RESET}`);
  console.log(`${BOLD}${CYAN}╚═══════════════════════════════════════════╝${RESET}`);

  // Load .env.local for the frontend context
  try {
    const fs = require("fs");
    const path = require("path");
    const envPath = path.join(__dirname, "../frontend/.env.local");
    if (fs.existsSync(envPath)) {
      const lines = fs.readFileSync(envPath, "utf8").split("\n");
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith("#")) continue;
        const eqIdx = trimmed.indexOf("=");
        if (eqIdx === -1) continue;
        const key = trimmed.slice(0, eqIdx).trim();
        const val = trimmed.slice(eqIdx + 1).trim();
        if (!process.env[key]) process.env[key] = val;
      }
      ok("Loaded", "frontend/.env.local");
    } else {
      warn("frontend/.env.local", "not found — running without env context");
    }
  } catch (e) {
    warn("env load", e.message);
  }

  checkEnv();
  checkNextAuthConfig();
  checkRouteConflicts();
  const backendUp = await checkBackend();
  if (backendUp) {
    await checkSocialExchange();
    await simulateSignInCallback();
    await checkJwtFlow();
    await checkUsersMe();
  }
  printSummary();
}

main().catch(console.error);
