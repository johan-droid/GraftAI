import { getSession } from "next-auth/react";

// ─── Base URL ────────────────────────────────────────────────────────────────

const rawApiBase =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://graftai.onrender.com";

const normalizedBase = rawApiBase.replace(/\/+$/, "");
const BASE_URL = normalizedBase.endsWith("/api/v1")
  ? normalizedBase
  : `${normalizedBase}/api/v1`;

export const API_BASE_URL = BASE_URL;

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ApiRequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | null | undefined>;
  json?: unknown;
  /** Set to true to skip the automatic 401 → refresh → retry logic */
  skipRefresh?: boolean;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

export function composeEndpoint(path: string, includeBaseUrl = false) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return includeBaseUrl ? `${BASE_URL}${normalized}` : normalized;
}

/**
 * Retrieve the backend JWT from whatever context we're in.
 * - Browser: use NextAuth's `getSession()` (works in React components & RSC)
 * - Server: caller should pass the token directly via `Authorization` header
 */
async function getAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  console.debug("[Auth Debug] getAuthToken env", {
    NEXTAUTH_URL: process.env.NEXTAUTH_URL,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL,
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
  });
  try {
    const session = await getSession();
    console.debug("[Auth Debug] getSession result", {
      status: session ? "ok" : "no-session",
      backendToken: !!(session as any)?.backendToken,
    });
    return (session as any)?.backendToken ?? null;
  } catch (error) {
    console.error("[Auth Debug] getSession error", error);
    try {
      const sessionUrl = `${window.location.origin}/api/auth/session`;
      const res = await fetch(sessionUrl, {
        method: "GET",
        credentials: "include",
        headers: { Accept: "application/json" },
      });
      const text = await res.text();
      console.error("[Auth Debug] /api/auth/session raw response", {
        url: sessionUrl,
        status: res.status,
        ok: res.ok,
        text: text.slice(0, 400),
      });
    } catch (innerError) {
      console.error("[Auth Debug] failed to fetch /api/auth/session", innerError);
    }
    return null;
  }
}

/**
 * Export so components that need the raw token can grab it.
 */
export { getAuthToken };

// ─── Client ──────────────────────────────────────────────────────────────────

export const apiClient = {
  async fetch(endpoint: string, options: ApiRequestOptions = {}) {
    const { params, json, skipRefresh, ...requestInit } = options;

    // 1. Build URL
    let url = `${BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
    if (params) {
      const sp = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null) {
          sp.append(key, String(value));
        }
      }
      const qs = sp.toString();
      if (qs) url += `?${qs}`;
    }

    // 2. Get auth token
    const token = await getAuthToken();

    // 3. Headers
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(requestInit.headers as Record<string, string>),
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    // 4. Body
    const body = json !== undefined ? JSON.stringify(json) : requestInit.body;

    // 5. Fetch
    let response: Response;
    try {
      response = await fetch(url, {
        credentials: "include",
        ...requestInit,
        headers,
        body,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Network error";
      throw new Error(`Failed to reach API at ${url}. ${message}`);
    }

    // 6. Handle 401 — attempt a one-time silent token refresh then retry
    if (response.status === 401 && !skipRefresh && typeof window !== "undefined") {
      const refreshed = await attemptSessionRefresh();
      if (refreshed) {
        // Retry with new token
        return this.fetch(endpoint, { ...options, skipRefresh: true });
      }
      // Refresh failed — throw so the caller (AuthProvider) can decide what to do
      throw new Error("Could not validate credentials");
    }

    // 7. Other errors
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      const errorMessage =
        typeof error.detail === "string"
          ? error.detail
          : typeof error.message === "string"
          ? error.message
          : JSON.stringify(error.detail ?? error.message ?? error);
      throw new Error(errorMessage || `API error: ${response.status}`);
    }

    // 8. No content
    if (response.status === 204) return null;

    return response.json();
  },

  get<T>(endpoint: string, options: ApiRequestOptions = {}): Promise<T> {
    return this.fetch(endpoint, { ...options, method: "GET" });
  },

  post<T>(endpoint: string, body?: unknown, options: ApiRequestOptions = {}): Promise<T> {
    return this.fetch(endpoint, { ...options, method: "POST", json: body });
  },

  patch<T>(endpoint: string, body?: unknown, options: ApiRequestOptions = {}): Promise<T> {
    return this.fetch(endpoint, { ...options, method: "PATCH", json: body });
  },

  delete<T>(endpoint: string, options: ApiRequestOptions = {}): Promise<T> {
    return this.fetch(endpoint, { ...options, method: "DELETE" });
  },

  put<T>(endpoint: string, body?: unknown, options: ApiRequestOptions = {}): Promise<T> {
    return this.fetch(endpoint, { ...options, method: "PUT", json: body });
  },
};

// ─── Silent token refresh helper ─────────────────────────────────────────────

let _refreshPromise: Promise<boolean> | null = null;

async function attemptSessionRefresh(): Promise<boolean> {
  // Deduplicate concurrent refresh attempts
  if (_refreshPromise) return _refreshPromise;

  _refreshPromise = (async () => {
    try {
      const session = await getSession();
      const refreshToken = (session as any)?.refreshToken;
      if (!refreshToken) return false;

      const res = await fetch(`${BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
        cache: "no-store",
      });

      return res.ok;
    } catch {
      return false;
    } finally {
      _refreshPromise = null;
    }
  })();

  return _refreshPromise;
}
