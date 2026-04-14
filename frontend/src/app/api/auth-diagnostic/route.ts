import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";

// This route is development-only and intentionally verbose
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  if (process.env.NODE_ENV === "production") {
    return NextResponse.json({ error: "Not Found" }, { status: 404 });
  }

  // ── 1. Read the current NextAuth session ──────────────────────────────────
  let session: any = null;
  let sessionError: string | null = null;
  try {
    session = await auth();
  } catch (e: any) {
    sessionError = e.message;
  }

  const backendToken  = session?.backendToken ?? null;
  const sessionError2 = session?.error ?? null;
  const sessionUser   = session?.user ?? null;

  // ── 2. Validate the backend token against /auth/check ────────────────────
  let backendCheckResult: any = null;
  if (backendToken) {
    try {
      const backendUrl =
        process.env.BACKEND_URL ||
        process.env.NEXT_PUBLIC_BACKEND_URL ||
        "http://127.0.0.1:8000";
      const res = await fetch(`${backendUrl}/api/v1/auth/check`, {
        headers: {
          Authorization: `Bearer ${backendToken}`,
          Accept: "application/json",
        },
        cache: "no-store",
      });
      backendCheckResult = {
        status: res.status,
        ok: res.ok,
        body: await res.json().catch(() => null),
      };
    } catch (e: any) {
      backendCheckResult = { error: e.message };
    }
  }

  // ── 3. Decode the backendToken claims without verifying ───────────────────
  let tokenClaims: any = null;
  if (backendToken) {
    try {
      const parts = backendToken.split(".");
      if (parts.length === 3) {
        const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
        tokenClaims = JSON.parse(Buffer.from(b64, "base64").toString());
        if (tokenClaims.exp) {
          const secondsLeft = tokenClaims.exp - Math.floor(Date.now() / 1000);
          tokenClaims._seconds_until_expiry = secondsLeft;
          tokenClaims._expired = secondsLeft < 0;
        }
      }
    } catch { /* ignore */ }
  }

  // ── 4. List cookies ───────────────────────────────────────────────────────
  const cookieHeader = req.headers.get("cookie") || "";
  const cookieNames = cookieHeader
    .split(";")
    .map((c) => c.trim().split("=")[0])
    .filter(Boolean);

  // ── 5. Check BACKEND_URL resolution ──────────────────────────────────────
  const rawBackendResolution =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000";
  const normalizedBackendResolution = rawBackendResolution.replace(/\/+$/, "");
  const resolvedBackendOrigin = normalizedBackendResolution.replace(/\/api\/v1$/, "");
  const resolvedApiBaseUrl = normalizedBackendResolution.endsWith("/api/v1")
    ? normalizedBackendResolution
    : `${resolvedBackendOrigin}/api/v1`;

  const backendUrlResolution = {
    BACKEND_URL:              process.env.BACKEND_URL ?? "(not set)",
    NEXT_PUBLIC_BACKEND_URL:  process.env.NEXT_PUBLIC_BACKEND_URL ?? "(not set)",
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "(not set)",
    NEXT_PUBLIC_API_URL:      process.env.NEXT_PUBLIC_API_URL ?? "(not set)",
    effectiveBackendOrigin: resolvedBackendOrigin,
    effectiveApiBaseUrl: resolvedApiBaseUrl,
  };

  const authUrlResolution = {
    NEXTAUTH_URL: process.env.NEXTAUTH_URL ?? "(not set)",
    AUTH_URL: process.env.AUTH_URL ?? "(not set)",
    AUTH_SECRET: !!process.env.AUTH_SECRET,
    NEXTAUTH_SECRET: !!process.env.NEXTAUTH_SECRET,
  };

  const wsUrlResolution = {
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL ?? "(not set)",
  };

  // ── 6. Provider credentials ───────────────────────────────────────────────
  const providers = {
    google: {
      clientId:     !!process.env.GOOGLE_CLIENT_ID,
      clientSecret: !!process.env.GOOGLE_CLIENT_SECRET,
    },
    microsoft: {
      clientId:     !!process.env.MICROSOFT_CLIENT_ID,
      clientSecret: !!process.env.MICROSOFT_CLIENT_SECRET,
      tenantId:     process.env.MICROSOFT_TENANT_ID ?? "(not set — defaults to common)",
    },
  };

  // ── 7. Assemble diagnosis ─────────────────────────────────────────────────
  const diagnosis: string[] = [];

  if (!session) {
    diagnosis.push("❌ No NextAuth session — user is NOT logged in (or signIn callback returned false)");
  } else if (!backendToken) {
    diagnosis.push("❌ Session exists but backendToken is missing — signIn callback likely failed silently");
  } else if (sessionError2 === "RefreshTokenError") {
    diagnosis.push("❌ RefreshTokenError — backend token refresh failed, AuthProvider will sign out");
  } else if (backendCheckResult?.ok) {
    diagnosis.push("✅ Session is valid — user is authenticated end-to-end");
  } else if (backendCheckResult?.status === 401) {
    diagnosis.push("❌ Backend rejects the token (401) — SECRET_KEY mismatch between NextAuth signIn and backend deps.py");
  } else {
    diagnosis.push(`⚠️ Backend check returned ${backendCheckResult?.status} — unusual`);
  }

  if (!providers.google.clientId || !providers.google.clientSecret) {
    diagnosis.push("❌ Google credentials missing");
  }
  if (!providers.microsoft.clientId || !providers.microsoft.clientSecret) {
    diagnosis.push("❌ Microsoft credentials missing — Microsoft login will fail");
  }
  if (!process.env.BACKEND_URL) {
    diagnosis.push("⚠️ BACKEND_URL not set — using NEXT_PUBLIC_ fallback (may be undefined in server context)");
  }

  return NextResponse.json({
    timestamp: new Date().toISOString(),
    diagnosis,
    authEnv: authUrlResolution,
    session: {
      exists: !!session,
      user: sessionUser,
      backendTokenPresent: !!backendToken,
      backendTokenClaims: tokenClaims,
      sessionError: sessionError2,
      expires: session?.expires ?? null,
    },
    backendValidation: backendCheckResult,
    backendUrlResolution,
    wsUrlResolution,
    providers,
    cookies: {
      names: cookieNames,
      hasNextAuthSession: cookieNames.some((n) => n.includes("next-auth") || n.includes("authjs")),
      hasLegacyCookies: cookieNames.some((n) =>
        ["auth_token", "graftai_access_token", "graftai_refresh_token"].includes(n)
      ),
    },
    sessionReadError: sessionError,
  }, { status: 200 });
}
