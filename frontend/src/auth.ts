import NextAuth, {
  type DefaultSession,
  type User,
  type Account,
  type Session,
} from "next-auth";
import type { NextAuthConfig } from "next-auth";
import type { JWT } from "@auth/core/jwt";
import CredentialsProvider from "next-auth/providers/credentials";
import { authConfig } from "./auth.config";
import { getGoogleOAuthCredentials, getMicrosoftOAuthCredentials } from "@/lib/oauth-env";

const googleOAuth = getGoogleOAuthCredentials();
const microsoftOAuth = getMicrosoftOAuthCredentials();

// Resolve Environment Variables
if (!process.env.NEXTAUTH_URL) {
  process.env.NEXTAUTH_URL =
    process.env.NEXT_PUBLIC_APP_URL ||
    (process.env.NODE_ENV === "production" ? "https://www.graftai.tech" : "http://localhost:3000");
}



/**
 * Resolve the backend base URL in a way that works for:
 *  - Next.js server components (Node.js runtime)
 *  - NextAuth callbacks (also Node.js, but env resolution can differ)
 * Prefer server-only BACKEND_URL env var first, then NEXT_PUBLIC_* variants.
 * Never falls back to a relative URL since server-side fetch requires absolute URLs.
 */
type SocialAuthAccount = Pick<
  Account,
  "provider" | "providerAccountId" | "access_token" | "id_token" | "refresh_token"
>;

type SocialAuthUser = Pick<User, "email" | "name" | "image">;

type CredentialsAuthUser = User & {
  backendToken: string;
  refreshToken?: string;
  backendTokenExpiresAt?: number;
};

type NextAuthJwt = JWT & {
  backendToken?: string;
  refreshToken?: string;
  backendTokenExpiresAt?: number;
  refreshRetryAt?: number;
  error?: "RefreshTokenError";
  provider?: string;
  userProfile?: {
    tier?: string;
    subscription_status?: string;
    daily_ai_count?: number;
    daily_ai_limit?: number;
    total_ai_tokens?: number;
    total_api_calls?: number;
    total_scheduling_count?: number;
  };
};

const AUTH_HTTP_TIMEOUT_MS = 15000;
const AUTH_EXCHANGE_TIMEOUT_MS = 45000;
const authGlobal = globalThis as typeof globalThis & {
  __graftaiPendingTokenCleanupInterval?: ReturnType<typeof setInterval>;
};

function getServerBackendUrl(): string {
  const url =
    process.env.BACKEND_URL ||
    process.env.INTERNAL_BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/api\/v1$/, "") ||
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/v1$/, "");

  if (!url) {
    if (process.env.NODE_ENV === "production") {
      console.warn(
        "Missing BACKEND_URL or NEXT_PUBLIC_BACKEND_URL environment variable. " +
        "Falling back to https://graftai-abu1.onrender.com for production."
      );
      return "https://graftai-abu1.onrender.com";
    } else {
      console.warn("Missing BACKEND_URL environment variable. Falling back to http://localhost:8000 for development.");
      return "http://localhost:8000";
    }
  }

  const normalized = url.replace(/\/+$/, "");

  // Dev hardening: Node/undici may resolve localhost to ::1 first while our
  // backend is bound to 127.0.0.1, which can cause long connection stalls.
  if (process.env.NODE_ENV !== "production") {
    try {
      const parsed = new URL(normalized);
      if (parsed.hostname === "localhost") {
        parsed.hostname = "127.0.0.1";
        return parsed.toString().replace(/\/+$/, "");
      }
    } catch {
      // Keep original URL if parsing fails.
    }
  }

  return normalized;
}

function getBackendApiUrl(): string {
  return `${getServerBackendUrl()}/api/v1`;
}

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init?: RequestInit,
  timeoutMs = AUTH_HTTP_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}

// ─── Extended Type Declarations ──────────────────────────────────────────────

declare module "next-auth" {
  interface User {
    backendToken?: string;
    refreshToken?: string;
    backendTokenExpiresAt?: number; // Unix timestamp (seconds)
  }
  interface Session {
    backendToken?: string;
    backendTokenExpiresAt?: number;
    user: {
      id: string;
      tier?: string;
      subscription_status?: string;
      daily_ai_count?: number;
      daily_ai_limit?: number;
      total_ai_tokens?: number;
      total_api_calls?: number;
      total_scheduling_count?: number;
    } & DefaultSession["user"];
    error?: "RefreshTokenError";
  }
}

declare module "@auth/core/jwt" {
  interface JWT {
    backendToken?: string;
    refreshToken?: string;
    backendTokenExpiresAt?: number;
    refreshRetryAt?: number;
    error?: "RefreshTokenError";
    provider?: string;
    userProfile?: {
      tier?: string;
      subscription_status?: string;
      daily_ai_count?: number;
      daily_ai_limit?: number;
      total_ai_tokens?: number;
      total_api_calls?: number;
      total_scheduling_count?: number;
    };
  }
}

// ─── Token Helpers ────────────────────────────────────────────────────────────

/**
 * Returns true only if we have a concrete expiry AND that expiry is imminent.
 * If expiresAt is undefined (e.g. first sign-in or decode failed), we consider
 * token valid to avoid an unnecessary refresh cycle that signs the user out.
 */
function isBackendTokenExpired(expiresAt?: number): boolean {
  if (!expiresAt) return false; // Treat unknown expiry as still valid
  // Refresh if less than 60 seconds remain
  return Date.now() / 1000 > expiresAt - 60;
}

function isWithinRetryCooldown(retryAt?: number): boolean {
  return typeof retryAt === "number" && Date.now() < retryAt;
}

type RefreshBackendResult =
  | { status: "ok"; access_token: string; refresh_token: string }
  | { status: "transient_fail"; reason: string; retryAfterMs?: number }
  | { status: "hard_fail"; reason: string };

// In-memory refresh locks to prevent concurrent refresh attempts
const _refreshLocks = new Map<string, Promise<RefreshBackendResult>>();

type RefreshRotationResult = {
  access_token: string;
  refresh_token: string;
  cachedAt: number;
};

const _recentRefreshResults = new Map<string, RefreshRotationResult>();
const RECENT_REFRESH_RESULT_TTL_MS = 2 * 60 * 1000;

function cleanupExpiredRefreshResults(): void {
  const now = Date.now();
  for (const [refreshToken, entry] of _recentRefreshResults.entries()) {
    if (now - entry.cachedAt > RECENT_REFRESH_RESULT_TTL_MS) {
      _recentRefreshResults.delete(refreshToken);
    }
  }
}

async function refreshBackendToken(refreshToken?: string): Promise<RefreshBackendResult> {
  if (!refreshToken) {
    return { status: "hard_fail", reason: "missing_refresh_token" };
  }

  const recentResult = _recentRefreshResults.get(refreshToken);
  if (recentResult && Date.now() - recentResult.cachedAt <= RECENT_REFRESH_RESULT_TTL_MS) {
    console.log("[NextAuth] Reusing recently rotated refresh token result");
    return {
      status: "ok",
      access_token: recentResult.access_token,
      refresh_token: recentResult.refresh_token,
    };
  }
  
  // Check if there's already a refresh in progress for this token
  const existingLock = _refreshLocks.get(refreshToken);
  if (existingLock) {
    console.log("[NextAuth] Refresh already in progress, waiting for result");
    return existingLock;
  }

  // Create the refresh promise and store it in the lock map
  const refreshPromise: Promise<RefreshBackendResult> = (async () => {
    try {
      const url = `${getBackendApiUrl()}/auth/refresh`;
      const res = await fetchWithTimeout(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
        credentials: "include",
        cache: "no-store",
      });
      const responseText = await res.text().catch(() => "");
      if (!res.ok) {
        if (res.status === 401 && /already been used|blacklisted/i.test(responseText)) {
          const cachedResult = _recentRefreshResults.get(refreshToken);
          if (cachedResult && Date.now() - cachedResult.cachedAt <= RECENT_REFRESH_RESULT_TTL_MS) {
            console.warn("[NextAuth] Refresh token was already rotated; using cached result");
            return {
              status: "ok",
              access_token: cachedResult.access_token,
              refresh_token: cachedResult.refresh_token,
            };
          }

          console.warn("[NextAuth] Refresh token was already rotated, but no cached result was available");
          return { status: "hard_fail", reason: "refresh_token_already_rotated_no_cache" };
        }

        if (res.status === 401 || res.status === 403) {
          console.error("[NextAuth] Hard refresh auth failure:", res.status, responseText);
          return { status: "hard_fail", reason: `http_${res.status}` };
        }

        const retryAfterHeader = res.headers.get("retry-after");
        const retryAfterMsRaw = retryAfterHeader ? Number.parseInt(retryAfterHeader, 10) : NaN;
        const retryAfterMs = Number.isFinite(retryAfterMsRaw) && retryAfterMsRaw > 0
          ? retryAfterMsRaw * 1000
          : undefined;
        console.error("[NextAuth] Refresh failed:", res.status, responseText);
        return {
          status: "transient_fail",
          reason: `http_${res.status}`,
          retryAfterMs,
        };
      }
      const result = parseJsonTextSafe<{
        access_token?: string;
        refresh_token?: string;
      }>(responseText);

      if (!result?.access_token || !result?.refresh_token) {
        console.error("[NextAuth] Refresh response missing access/refresh token");
        return { status: "transient_fail", reason: "missing_tokens_in_refresh_response" };
      }

      _recentRefreshResults.set(refreshToken, {
        access_token: result.access_token,
        refresh_token: result.refresh_token,
        cachedAt: Date.now(),
      });
      console.log("[NextAuth] Refresh successful");
      return {
        status: "ok",
        access_token: result.access_token,
        refresh_token: result.refresh_token,
      };
    } catch (err) {
      const isAbort = (err as { name?: string })?.name === "AbortError";
      console.error("[NextAuth] Refresh error:", err);
      return {
        status: "transient_fail",
        reason: isAbort ? "refresh_timeout" : "refresh_network_error",
      };
    } finally {
      // Clean up the lock after completion
      _refreshLocks.delete(refreshToken);
      cleanupExpiredRefreshResults();
    }
  })();

  // Store the promise in the lock map
  _refreshLocks.set(refreshToken, refreshPromise);
  
  return refreshPromise;
}

/**
 * Safely decode the `exp` field from a JWT without any external library.
 * Falls back to undefined if the token is malformed.
 */
function decodeJwtExpiry(token: string): number | undefined {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return undefined;
    // Use Buffer in Node.js runtime; no-op safe for Edge
    const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const json =
      typeof Buffer !== "undefined"
        ? Buffer.from(b64, "base64").toString()
        : atob(b64);
    const payload = JSON.parse(json);
    return typeof payload.exp === "number" ? payload.exp : undefined;
  } catch {
    return undefined;
  }
}

function decodeJwtSubject(token: string): string | undefined {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return undefined;
    const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const json =
      typeof Buffer !== "undefined"
        ? Buffer.from(b64, "base64").toString()
        : atob(b64);
    const payload = JSON.parse(json);
    return typeof payload.sub === "string" && payload.sub.trim() !== ""
      ? payload.sub
      : undefined;
  } catch {
    return undefined;
  }
}

async function parseJsonSafe<T>(response: Response): Promise<T | null> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as T;
  } catch (error) {
    console.error("Failed to parse JSON response:", error, "body:", text);
    return null;
  }
}

function parseJsonTextSafe<T>(text: string): T | null {
  if (!text?.trim()) return null;
  try {
    return JSON.parse(text) as T;
  } catch (error) {
    console.error("Failed to parse JSON text:", error, "body:", text);
    return null;
  }
}

function createCredentialsProvider() {
  return CredentialsProvider({
    name: "Credentials",
    credentials: {
      email: { label: "Email", type: "email" },
      password: { label: "Password", type: "password" },
    },
    async authorize(credentials) {
      if (!credentials?.email || !credentials?.password) {
        throw new Error("Missing credentials");
      }

      const email = String(credentials.email);
      const password = String(credentials.password);
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const res = await fetchWithTimeout(`${getBackendApiUrl()}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      const data = await parseJsonSafe<{ detail?: string; access_token?: string; refresh_token?: string }>(res);
      if (!res.ok) {
        throw new Error((data?.detail && String(data.detail)) || "Authentication failed");
      }

      const accessToken = data?.access_token;
      if (!accessToken) {
        throw new Error("Authentication succeeded but no access token was returned.");
      }

      const userRes = await fetchWithTimeout(`${getBackendApiUrl()}/users/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      if (!userRes.ok) {
        const body = await userRes.text().catch(() => "");
        throw new Error(`Failed fetching user profile: ${userRes.status} ${body}`);
      }

      const userData = await parseJsonSafe<Record<string, unknown>>(userRes);
      if (!userData) {
        throw new Error("User profile response contained no JSON.");
      }

      const userId = typeof userData.id === "string" ? userData.id.trim() : "";
      if (!userId) {
        throw new Error("User profile response is missing a valid id.");
      }

      return {
        id: userId,
        email: String(userData.email ?? email),
        name: String(userData.name ?? email),
        role: String(userData.role ?? "user"),
        backendToken: accessToken,
        refreshToken: data?.refresh_token,
      };
    }
  });
}

// Token handoff storage with TTL for cleanup
const PENDING_TOKEN_TTL_MS = 5 * 60 * 1000; // 5 minutes
const CLEANUP_INTERVAL_MS = 60 * 1000; // Cleanup every minute

interface PendingTokenEntry {
  backendToken: string;
  refreshToken: string;
  backendUserId?: string;
  backendTokenExpiresAt: number | undefined;
  userProfile?: {
    tier?: string;
    subscription_status?: string;
    daily_ai_count?: number;
    daily_ai_limit?: number;
    total_ai_tokens?: number;
    total_api_calls?: number;
    total_scheduling_count?: number;
  };
  createdAt: number; // Timestamp for TTL cleanup
}

interface BackendExchangeTokens {
  access_token: string;
  refresh_token: string;
  user?: {
    id?: string;
    tier?: string;
    subscription_status?: string;
    daily_ai_count?: number;
    daily_ai_limit?: number;
    total_ai_tokens?: number;
    total_api_calls?: number;
    total_scheduling_count?: number;
  };
}

const _pendingBackendTokens = new Map<string, PendingTokenEntry>();

// Periodic cleanup to prevent memory leaks
function cleanupExpiredTokens(): void {
  const now = Date.now();
  let cleaned = 0;
  for (const [key, entry] of _pendingBackendTokens.entries()) {
    if (now - entry.createdAt > PENDING_TOKEN_TTL_MS) {
      _pendingBackendTokens.delete(key);
      cleaned++;
    }
  }
  if (cleaned > 0) {
    console.warn(`[NextAuth] Cleaned up ${cleaned} expired pending token entries`);
  }
}

// Start the cleanup loop once per server process to avoid duplicate intervals
// during hot reloads or repeated module evaluation.
if (
  typeof window === "undefined" &&
  process.env.NODE_ENV !== "test" &&
  !authGlobal.__graftaiPendingTokenCleanupInterval
) {
  authGlobal.__graftaiPendingTokenCleanupInterval = setInterval(
    cleanupExpiredTokens,
    CLEANUP_INTERVAL_MS,
  );
}

async function exchangeBackendTokens(
  account: SocialAuthAccount,
  user: SocialAuthUser,
): Promise<BackendExchangeTokens | null> {
  const url = `${getBackendApiUrl()}/auth/social/exchange`;
  try {
    console.log(`[NextAuth:exchangeBackendTokens] Starting POST ${url} (timeout=${AUTH_EXCHANGE_TIMEOUT_MS}ms)`);
    const res = await fetchWithTimeout(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: account.provider,
        provider_account_id: account.providerAccountId,
        email: user.email,
        name: user.name,
        image: user.image,
        access_token: account.access_token,
        id_token: account.id_token,
        refresh_token: account.refresh_token,
      }),
      cache: "no-store",
    }, AUTH_EXCHANGE_TIMEOUT_MS);

    const responseText = await res.text();
    console.log(`[NextAuth:exchangeBackendTokens] POST ${url} -> ${res.status}`);
    if (!res.ok) {
      console.error(`[NextAuth:exchangeBackendTokens] Backend rejected: ${res.status} — ${responseText}`);
      return null;
    }

    const parsed = parseJsonTextSafe<{
      access_token?: string;
      refresh_token?: string;
      user?: {
        id?: string;
        tier?: string;
        subscription_status?: string;
        daily_ai_count?: number;
        daily_ai_limit?: number;
        total_ai_tokens?: number;
        total_api_calls?: number;
        total_scheduling_count?: number;
      };
    }>(responseText);

    if (!parsed?.access_token || !parsed?.refresh_token) {
      console.error("[NextAuth:exchangeBackendTokens] Missing access/refresh token in backend response");
      return null;
    }

    return {
      access_token: parsed.access_token,
      refresh_token: parsed.refresh_token,
      user: parsed.user,
    };
  } catch (error) {
    if ((error as { name?: string })?.name === "AbortError") {
      console.error(
        `[NextAuth:exchangeBackendTokens] Timed out after ${AUTH_EXCHANGE_TIMEOUT_MS}ms calling backend exchange endpoint`,
      );
      return null;
    }
    console.error("[NextAuth:exchangeBackendTokens] Network error calling backend:", error);
    return null;
  }
}

// ─── NextAuth Config ──────────────────────────────────────────────────────────

// ─── NextAuth Secret ───────────────────────────────────────────────────────────
// In production, the secret MUST be provided via environment variable.
// The secret is used to encrypt session tokens - using a hardcoded value
// would allow anyone to forge session tokens.

const getNextAuthSecret = (): string => {
  const secret = process.env.NEXTAUTH_SECRET || process.env.AUTH_SECRET;
  
  // In production, fail closed if secret is missing or weak.
  if (process.env.NODE_ENV === "production") {
    if (!secret) {
      throw new Error(
        "[NextAuth] NEXTAUTH_SECRET (or AUTH_SECRET) is required in production. " +
        "Refusing to start with an insecure fallback secret."
      );
    }
    if (secret.length < 32) {
      throw new Error(
        "[NextAuth] NEXTAUTH_SECRET (or AUTH_SECRET) must be at least 32 characters in production."
      );
    }
    return secret;
  }
  
  // In development, use a default only if no secret is provided
  if (!secret) {
    console.warn("[NextAuth] Using development fallback secret. Set NEXTAUTH_SECRET for production.");
    return "dev-fallback-secret-change-in-production-32charsmin";
  }
  
  return secret;
};

export const nextAuthSecret = getNextAuthSecret();

const authOptions: NextAuthConfig = {
  ...authConfig,
  secret: nextAuthSecret,
  trustHost: true,
  providers: [...authConfig.providers, createCredentialsProvider()],

  callbacks: {
    ...authConfig.callbacks,
    // ─── signIn: called right after the provider authenticates ────────────
    async signIn({ user, account }: { user: User | null; account?: Account | null }) {
      if (!account || !user?.email) {
        console.error("[NextAuth:signIn] Missing account/email — aborting");
        return false;
      }

      if (account.provider === "credentials") {
        console.log(`[NextAuth:signIn] Credentials sign-in accepted for ${user.email}`);
        return true;
      }

      console.log(`[NextAuth:signIn] Handshaking with backend for ${user.email} via ${account.provider}`);
      
      // Perform early exchange to validate user exists/can sign in on backend
      const data = await exchangeBackendTokens(account, user);
      if (!data) {
        console.error("[NextAuth:signIn] Backend exchange failed during initial handshake");
        return false;
      }

      // Store in memory for immediate handoff to the jwt callback
      const mapKey = `${account.provider}:${account.providerAccountId}`;
      _pendingBackendTokens.set(mapKey, {
        backendToken: data.access_token,
        refreshToken: data.refresh_token,
        backendUserId: data.user?.id || decodeJwtSubject(data.access_token),
        backendTokenExpiresAt: decodeJwtExpiry(data.access_token),
        userProfile: {
          tier: data.user?.tier,
          subscription_status: data.user?.subscription_status,
          daily_ai_count: data.user?.daily_ai_count,
          daily_ai_limit: data.user?.daily_ai_limit,
          total_ai_tokens: data.user?.total_ai_tokens,
          total_api_calls: data.user?.total_api_calls,
          total_scheduling_count: data.user?.total_scheduling_count,
        },
        createdAt: Date.now(),
      });

      return true;
    },

    // ─── jwt: persists tokens in the encrypted NextAuth cookie ────────────
    async jwt({ token, user, account }: { token: NextAuthJwt; user?: User | null; account?: Account | null }) {
      // Internal Auth Handshake: initial sign-in
      if (user && account) {
        if (account.provider === "credentials") {
          const credentialUser = user as CredentialsAuthUser;
          if (typeof credentialUser.backendToken === "string") {
            token.backendToken = credentialUser.backendToken;
            token.refreshToken = credentialUser.refreshToken;
            token.backendTokenExpiresAt =
              credentialUser.backendTokenExpiresAt ??
              decodeJwtExpiry(credentialUser.backendToken);
            token.sub =
              credentialUser.id ||
              decodeJwtSubject(credentialUser.backendToken) ||
              token.sub;
            token.userProfile = {
              tier: (credentialUser as any).tier,
              subscription_status: (credentialUser as any).subscription_status,
              daily_ai_count: (credentialUser as any).daily_ai_count,
              daily_ai_limit: (credentialUser as any).daily_ai_limit,
              total_ai_tokens: (credentialUser as any).total_ai_tokens,
              total_api_calls: (credentialUser as any).total_api_calls,
              total_scheduling_count: (credentialUser as any).total_scheduling_count,
            };
            token.provider = "credentials";
            token.error = undefined;
          } else {
            console.error("[NextAuth:jwt] Credentials sign-in did not return a backend token");
            token.error = "RefreshTokenError";
          }
          return token;
        }

        const mapKey = `${account.provider}:${account.providerAccountId}`;
        let pending = _pendingBackendTokens.get(mapKey);
        
        // If not in map (e.g. serverless instance mismatch), retry exchange
        if (!pending) {
          console.warn(`[NextAuth:jwt] Handoff miss for ${mapKey} — Retrying exchange.`);
          const data = await exchangeBackendTokens(account, user);
          if (data) {
            pending = {
              backendToken: data.access_token,
              refreshToken: data.refresh_token,
              backendUserId: data.user?.id || decodeJwtSubject(data.access_token),
              backendTokenExpiresAt: decodeJwtExpiry(data.access_token),
              userProfile: {
                tier: data.user?.tier,
                subscription_status: data.user?.subscription_status,
                daily_ai_count: data.user?.daily_ai_count,
                daily_ai_limit: data.user?.daily_ai_limit,
                total_ai_tokens: data.user?.total_ai_tokens,
                total_api_calls: data.user?.total_api_calls,
                total_scheduling_count: data.user?.total_scheduling_count,
              },
              createdAt: Date.now(),
            };
          }
        }

        if (pending) {
          _pendingBackendTokens.delete(mapKey); // Clean up
          token.backendToken = pending.backendToken;
          token.refreshToken = pending.refreshToken;
          token.backendTokenExpiresAt = pending.backendTokenExpiresAt;
          token.sub = pending.backendUserId || token.sub;
          token.userProfile = pending.userProfile;
          token.provider = account.provider;
          token.error = undefined;
        } else {
          console.error(`[NextAuth:jwt] ❌ FAILED_TO_ESTABLISH_BACKEND_TRUST for ${mapKey}`);
          token.error = "RefreshTokenError";
        }
        return token;
      }

      // Subsequent requests — silently refresh if near-expiry
      if (token.error === "RefreshTokenError") {
        return token;
      }

      if (isWithinRetryCooldown(token.refreshRetryAt)) {
        return token;
      }

      if (!isBackendTokenExpired(token.backendTokenExpiresAt)) {
        return token; // Still valid
      }

      console.log(`[NextAuth:jwt] Token expired/near-expiry — attempting silent refresh`);
      const refreshed = await refreshBackendToken(token.refreshToken);
      if (refreshed.status === "ok") {
        token.backendToken = refreshed.access_token;
        token.refreshToken = refreshed.refresh_token;
        token.backendTokenExpiresAt = decodeJwtExpiry(refreshed.access_token);
        token.refreshRetryAt = undefined;
        token.error = undefined;
        console.log(`[NextAuth:jwt] ✅ Token refreshed`);
      } else {
        const accessTokenStillValid = typeof token.backendTokenExpiresAt === "number" && Date.now() / 1000 < token.backendTokenExpiresAt;
        if (refreshed.status === "transient_fail") {
          const retryAfterMs =
            typeof refreshed.retryAfterMs === "number" && refreshed.retryAfterMs > 0
              ? refreshed.retryAfterMs
              : 30_000;
          token.refreshRetryAt = Date.now() + retryAfterMs;
          token.error = undefined;
          console.warn(
            `[NextAuth:jwt] Refresh transient failure (${refreshed.reason || "unknown"}) — retrying shortly`
          );
        } else if (refreshed.reason === "refresh_token_already_rotated_no_cache") {
          // Race-condition guard: another concurrent request likely rotated the token.
          // Give the session cookie a chance to converge before forcing sign-out.
          token.refreshRetryAt = Date.now() + 5_000;
          token.error = undefined;
          console.warn(
            "[NextAuth:jwt] Refresh token rotation race detected (no cache replay yet) — retrying shortly"
          );
        } else if (accessTokenStillValid) {
          token.refreshRetryAt = Date.now() + 15_000;
          token.error = undefined;
          console.warn(`[NextAuth:jwt] Refresh hard-failed but access token is still valid — retrying shortly`);
        } else {
          console.error(
            `[NextAuth:jwt] ❌ Refresh hard failure (${refreshed.reason || "unknown"}) — stamping RefreshTokenError`
          );
          token.error = "RefreshTokenError";
          token.backendToken = undefined;
          token.refreshRetryAt = undefined;
        }
      }

      return token;
    },

    // ─── session: exposes safe data to the frontend ────────────────────────
    async session({ session, token }: { session: Session; token: NextAuthJwt }) {
      // Propagate backend token and expiry
      session.backendToken = token.backendToken;
      session.backendTokenExpiresAt = token.backendTokenExpiresAt;
      session.error = token.error as "RefreshTokenError" | undefined;

      // Ensure the session user has a stable `id` from the JWT subject
      if (token.sub) {
        session.user.id = token.sub;
      }
      
      // Propagate usage fields to frontend
      if (token.userProfile) {
        session.user.tier = token.userProfile.tier;
        session.user.subscription_status = token.userProfile.subscription_status;
        session.user.daily_ai_count = token.userProfile.daily_ai_count;
        session.user.daily_ai_limit = token.userProfile.daily_ai_limit;
        session.user.total_ai_tokens = token.userProfile.total_ai_tokens;
        session.user.total_api_calls = token.userProfile.total_api_calls;
        session.user.total_scheduling_count = token.userProfile.total_scheduling_count;
      }

      return session;
    },
  },
};

export const { handlers, signIn, signOut, auth } = NextAuth(authOptions);
