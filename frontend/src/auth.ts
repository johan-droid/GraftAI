import NextAuth, { type NextAuthConfig, type DefaultSession } from "next-auth";
import { type JWT } from "next-auth/jwt";
import GoogleProvider from "next-auth/providers/google";
import MicrosoftEntraId from "next-auth/providers/microsoft-entra-id";

/**
 * Resolve the backend base URL in a way that works for:
 *  - Next.js server components (Node.js runtime)
 *  - NextAuth callbacks (also Node.js, but env resolution can differ)
 * Prefer server-only BACKEND_URL env var first, then NEXT_PUBLIC_* variants.
 * Never falls back to a relative URL since server-side fetch requires absolute URLs.
 */
function getServerBackendUrl(): string {
  return (
    process.env.BACKEND_URL ||
    process.env.INTERNAL_BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/api\/v1$/, "") ||
    "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
}

function getBackendApiUrl(): string {
  return `${getServerBackendUrl()}/api/v1`;
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
    } & DefaultSession["user"];
    error?: "RefreshTokenError";
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    backendToken?: string;
    refreshToken?: string;
    backendTokenExpiresAt?: number;
    error?: "RefreshTokenError";
    // Provider OAuth tokens (for calendar integration)
    providerAccessToken?: string;
    providerRefreshToken?: string;
    provider?: string;
  }
}

// ─── Token Helpers ────────────────────────────────────────────────────────────

/**
 * Returns true only if we have a concrete expiry AND that expiry is imminent.
 * If expiresAt is undefined (e.g. first sign-in or decode failed), we consider
 * the token valid to avoid an unnecessary refresh cycle that signs the user out.
 */
function isBackendTokenExpired(expiresAt?: number): boolean {
  if (!expiresAt) return false; // Treat unknown expiry as still valid
  // Refresh if less than 60 seconds remain
  return Date.now() / 1000 > expiresAt - 60;
}

async function refreshBackendToken(refreshToken?: string): Promise<{
  access_token: string;
  refresh_token: string;
} | null> {
  if (!refreshToken) return null;
  try {
    const url = `${getBackendApiUrl()}/auth/refresh`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    });
    if (!res.ok) {
      console.error("[NextAuth] Refresh failed:", res.status, await res.text().catch(() => ""));
      return null;
    }
    return await res.json();
  } catch (err) {
    console.error("[NextAuth] Refresh error:", err);
    return null;
  }
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

/**
 * NextAuth v5 (beta) does NOT allow passing custom data through the `user`
 * object from signIn → jwt. We use a short-lived in-memory map keyed by
 * the provider account ID to bridge the gap.
 *
 * The entry is consumed (deleted) by the jwt callback on the initial sign-in
 * request, so it only lives in memory for a few milliseconds.
 */
const _pendingBackendTokens = new Map<string, {
  backendToken: string;
  refreshToken: string;
  backendTokenExpiresAt: number | undefined;
}>();

// ─── NextAuth Config ──────────────────────────────────────────────────────────

const nextAuthSecret =
  process.env.NEXTAUTH_SECRET ||
  process.env.AUTH_SECRET ||
  "your-development-fallback-secret-here";

if (process.env.NODE_ENV === "production" && !process.env.NEXTAUTH_SECRET && !process.env.AUTH_SECRET) {
  console.warn("[NextAuth] NEXTAUTH_SECRET/AUTH_SECRET is missing in production!");
}

const authOptions: NextAuthConfig = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
      authorization: {
        params: {
          // Request calendar access + offline access for refresh tokens
          scope: [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
          ].join(" "),
          access_type: "offline",
          prompt: "consent", // Force consent to always get refresh_token
        },
      },
    }),
    MicrosoftEntraId({
      clientId: process.env.MICROSOFT_CLIENT_ID || "",
      clientSecret: process.env.MICROSOFT_CLIENT_SECRET || "",
      issuer: `https://login.microsoftonline.com/${process.env.MICROSOFT_TENANT_ID || "common"}/v2.0`,
      authorization: {
        params: {
          // Request calendar access + offline access for refresh tokens
          scope: [
            "openid",
            "email",
            "profile",
            "offline_access",
            "Calendars.ReadWrite",
            "User.Read",
          ].join(" "),
        },
      },
    }),
  ],

  pages: {
    signIn: "/login",
    error: "/login",
  },

  callbacks: {
    // ─── signIn: called right after the provider authenticates ────────────
    async signIn({ user, account }) {
      if (!account) {
        console.error("[NextAuth:signIn] No account object — aborting");
        return false;
      }

      const url = `${getBackendApiUrl()}/auth/social/exchange`;
      console.log(`[NextAuth:signIn] provider=${account.provider} email=${user.email}`);
      console.log(`[NextAuth:signIn] Calling backend: POST ${url}`);
      console.log(`[NextAuth:signIn] access_token present: ${!!account.access_token}, id_token: ${!!account.id_token}`);

      try {
        const res = await fetch(url, {
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
        });

        const responseText = await res.text();
        console.log(`[NextAuth:signIn] Backend response: ${res.status} — ${responseText.slice(0, 200)}`);

        if (res.ok) {
          const data = JSON.parse(responseText);
          // Store in the pending map so the jwt callback can pick it up
          // Key: providerAccountId (unique per OAuth login)
          const mapKey = `${account.provider}:${account.providerAccountId}`;
          _pendingBackendTokens.set(mapKey, {
            backendToken: data.access_token,
            refreshToken: data.refresh_token,
            backendTokenExpiresAt: decodeJwtExpiry(data.access_token),
          });
          console.log(`[NextAuth:signIn] ✅ Backend token stored (key=${mapKey})`);
          return true;
        }

        console.error(`[NextAuth:signIn] ❌ Backend rejected: ${res.status} — ${responseText}`);
        return false;
      } catch (error) {
        console.error("[NextAuth:signIn] ❌ Network error calling backend:", error);
        return false;
      }
    },

    // ─── jwt: persists tokens in the encrypted NextAuth cookie ────────────
    async jwt({ token, user, account }) {
      // Initial sign-in — `user` and `account` are present only on first call
      if (user && account) {
        const mapKey = `${account.provider}:${account.providerAccountId}`;
        const pending = _pendingBackendTokens.get(mapKey);
        console.log(`[NextAuth:jwt] Initial sign-in. mapKey=${mapKey} pendingFound=${!!pending}`);

        if (pending) {
          _pendingBackendTokens.delete(mapKey); // consume immediately
          token.backendToken = pending.backendToken;
          token.refreshToken = pending.refreshToken;
          token.backendTokenExpiresAt = pending.backendTokenExpiresAt;
          token.providerAccessToken = account.access_token ?? undefined;
          token.providerRefreshToken = account.refresh_token ?? undefined;
          token.provider = account.provider;
          token.error = undefined;
          console.log(`[NextAuth:jwt] ✅ Backend token assigned. exp=${pending.backendTokenExpiresAt}`);
        } else {
          // signIn may have failed or the map was already consumed — flag it
          console.error(`[NextAuth:jwt] ❌ No pending token found for key=${mapKey} — signIn probably returned false`);
          token.error = "RefreshTokenError";
        }
        return token;
      }

      // Subsequent requests — silently refresh if near-expiry
      if (!isBackendTokenExpired(token.backendTokenExpiresAt)) {
        return token; // Still valid
      }

      console.log(`[NextAuth:jwt] Token expired/near-expiry — attempting silent refresh`);
      const refreshed = await refreshBackendToken(token.refreshToken);
      if (refreshed) {
        token.backendToken = refreshed.access_token;
        token.refreshToken = refreshed.refresh_token;
        token.backendTokenExpiresAt = decodeJwtExpiry(refreshed.access_token);
        token.error = undefined;
        console.log(`[NextAuth:jwt] ✅ Token refreshed`);
      } else {
        console.error(`[NextAuth:jwt] ❌ Refresh failed — stamping RefreshTokenError`);
        token.error = "RefreshTokenError";
        token.backendToken = undefined;
      }

      return token;
    },

    // ─── session: exposes safe data to the frontend ────────────────────────
    async session({ session, token }) {
      // Propagate backend token and expiry
      session.backendToken = token.backendToken;
      session.backendTokenExpiresAt = token.backendTokenExpiresAt;
      session.error = token.error as "RefreshTokenError" | undefined;

      // Ensure the session user has a stable `id` from the JWT subject
      if (token.sub) {
        session.user.id = token.sub;
      }

      return session;
    },
  },

  secret: nextAuthSecret,
};

export const { handlers, signIn, signOut, auth } = NextAuth(authOptions);
