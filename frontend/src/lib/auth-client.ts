type AuthError = { message: string };
type AuthResult<T = unknown> = { data: T | null; error: AuthError | null };

function getApiBaseUrl() {
  if (typeof window !== "undefined") {
    // Force relative paths in the browser to ensure requests use the Next.js proxy.
    // This is CRITICAL for cross-domain auth to work via Vercel/Render.
    return "";
  }
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_URL;
  if (envUrl) {
    return envUrl.replace(/\/+$/g, "");
  }
  return "http://localhost:8000";
}

const API_BASE_URL = getApiBaseUrl();

function authEndpoint(path: string): string {
  const cleanedPath = `/${path.replace(/^\/+/, "")}`;
  const fullPath = cleanedPath.startsWith("/api/v1") ? cleanedPath : `/api/v1${cleanedPath}`;
  return API_BASE_URL ? `${API_BASE_URL}${fullPath}` : fullPath;
}

async function parseError(res: Response): Promise<AuthError> {
  const raw = await res.text().catch(() => "");
  if (!raw) return { message: `Request failed with ${res.status}` };
  try {
    const data = JSON.parse(raw) as { detail?: string; error?: string; message?: string };
    return { message: data.detail || data.error || data.message || raw };
  } catch {
    return { message: raw };
  }
}

let _cachedToken: string | null = null;
let _cacheExpiry = 0;
const SESSION_CACHE_TTL_MS = 30_000;
let _refreshInFlight: Promise<boolean> | null = null;
let _providerAvailabilityCache: { providers: string[]; fetchedAt: number } | null = null;
const PROVIDER_CACHE_TTL_MS = 60_000;

export function getToken(): string | null {
  if (typeof document === "undefined") return null;
  
  // 1. Try Cookies
  const value = `; ${document.cookie}`;
  const parts = value.split(`; graftai_access_token=`);
  let token = parts.length === 2 ? parts.pop()?.split(";").shift() || null : null;
  
  // 2. Try SessionStorage
  if (!token) {
    try {
      if (typeof window !== "undefined" && window.sessionStorage) {
        token = window.sessionStorage.getItem("graftai_access_token");
      }
    } catch (e) { /* ignore */ }
  }

  // 3. Try LocalStorage (Persistence Fallback)
  if (!token) {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        token = window.localStorage.getItem("graftai_access_token");
      }
    } catch (e) { /* ignore */ }
  }

  // 4. Try URL query params for one-time SSO handoff token bridge
  if (!token && typeof window !== "undefined") {
    try {
      const params = new URLSearchParams(window.location.search);
      token = params.get("token") || params.get("access_token") || null;
      if (token && typeof window !== "undefined") {
        // Persist token into storage so future requests don't need URL fallback.
        window.sessionStorage?.setItem("graftai_access_token", token);
        window.localStorage?.setItem("graftai_access_token", token);
      }
    } catch (e) {
      /* ignore malformed URLs */
    }
  }

  // ROBUSTNESS: If we found a token in any source, sync it to others for redundancy
  if (token && typeof window !== "undefined") {
    try {
      if (window.sessionStorage && !window.sessionStorage.getItem("graftai_access_token")) {
        window.sessionStorage.setItem("graftai_access_token", token);
      }
      if (window.localStorage && !window.localStorage.getItem("graftai_access_token")) {
        window.localStorage.setItem("graftai_access_token", token);
      }
    } catch (e) { /* ignore */ }
  }

  return token;
}

export async function getAuthToken(): Promise<string | null> {
  const now = Date.now();
  if (_cachedToken && now < _cacheExpiry) {
    return _cachedToken;
  }

  try {
    const token = getToken();
    if (token) return token;
    
    // Last resort: fetch from server
    const session = await getSessionSafe();
    const serverToken = session?.data?.session?.token ?? null;
    _cachedToken = serverToken;
    _cacheExpiry = now + SESSION_CACHE_TTL_MS;
    return serverToken;
  } catch {
    return null;
  }
}

export function invalidateSessionCache(): void {
  _cachedToken = null;
  _cacheExpiry = 0;
  if (typeof window !== "undefined") {
    try {
      sessionStorage.removeItem("graftai_access_token");
      localStorage.removeItem("graftai_access_token");
      // Expire cookie
      document.cookie = "graftai_access_token=; path=/; max-age=0;";
    } catch (e) { /* ignore */ }
  }
}

export function getCsrfHeaders(): Record<string, string> {
  if (typeof document === "undefined") return {};
  const value = `; ${document.cookie}`;
  const parts = value.split(`; xsrf-token=`);
  const token = parts.length === 2 ? parts.pop()?.split(";").shift() || null : null;
  if (!token) return {};
  return {
    "X-XSRF-TOKEN": token,
    "x-xsrf-token": token,
  };
}

function getRefreshTokenFromClientStorage(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const sessionToken = window.sessionStorage?.getItem("graftai_refresh_token");
    if (sessionToken) return sessionToken;
  } catch {
    // ignore
  }
  try {
    const localToken = window.localStorage?.getItem("graftai_refresh_token");
    if (localToken) return localToken;
  } catch {
    // ignore
  }
  return null;
}

async function tryRefreshSession(): Promise<boolean> {
  if (_refreshInFlight) {
    return _refreshInFlight;
  }

  _refreshInFlight = (async () => {
    try {
      const refreshToken = getRefreshTokenFromClientStorage();
      const hasBodyToken = typeof refreshToken === "string" && refreshToken.trim().length > 0;

      const res = await fetch(authEndpoint("/auth/refresh"), {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
          ...(hasBodyToken ? { "Content-Type": "application/json" } : {}),
        },
        body: hasBodyToken ? JSON.stringify({ refresh_token: refreshToken }) : undefined,
      });
      return res.ok;
    } catch {
      return false;
    } finally {
      _refreshInFlight = null;
    }
  })();

  return _refreshInFlight;
}

async function getAvailableSocialProviders(): Promise<string[]> {
  const now = Date.now();
  if (_providerAvailabilityCache && now - _providerAvailabilityCache.fetchedAt < PROVIDER_CACHE_TTL_MS) {
    return _providerAvailabilityCache.providers;
  }

  try {
    const res = await fetch("/api/auth/providers", {
      method: "GET",
      credentials: "include",
      headers: { Accept: "application/json" },
    });

    if (!res.ok) {
      return [];
    }

    const data = (await res.json().catch(() => ({}))) as { providers?: string[] };
    const providers = Array.isArray(data.providers) ? data.providers : [];
    _providerAvailabilityCache = { providers, fetchedAt: now };
    return providers;
  } catch {
    return [];
  }
}

export const getSessionSafe = async (allowRefreshRetry = true) => {
  try {
    const headers: Record<string, string> = {
      Accept: "application/json",
    };

    const token = getToken();
    if (token) {
      // Standard header
      headers.Authorization = `Bearer ${token}`;
      // Backup header (Some proxies strip Authorization but leave custom ones)
      headers["X-Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(authEndpoint("/auth/check"), {
      method: "GET",
      credentials: "include",
      headers,
    });

    if (!res.ok) {
      if (res.status === 401) {
        if (allowRefreshRetry) {
          const refreshed = await tryRefreshSession();
          if (refreshed) {
            return await getSessionSafe(false);
          }
          const err = await parseError(res);
          return { data: null, error: err };
        }
        // Only clear local state after a failed post-refresh re-check.
        console.warn("[AUTH_CLIENT]: 401 Unauthorized from backend. Clearing local session state.");
        invalidateSessionCache();
      }
      const err = await parseError(res);
      return { data: null, error: err };
    }

    const data = await res.json();
    if (!data?.authenticated) {
      return { data: null, error: { message: "Session not authenticated" } };
    }

    return { data, error: null };
  } catch (err) {
    console.error("[AUTH_CLIENT]: Unexpected session fetch error:", err);
    return {
      data: null,
      error: { message: err instanceof Error ? err.message : "Failed to fetch session" },
    };
  }
};

export const signOut = async () => {
  try {
    const res = await fetch(authEndpoint("/auth/logout"), {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
    });

    if (!res.ok) {
      const error = await parseError(res);
      return { data: null, error };
    }

    invalidateSessionCache();
    return { data: await res.json().catch(() => ({ success: true })), error: null };
  } catch (err) {
    console.error("[AUTH_CLIENT]: Sign-out error:", err);
    return {
      data: null,
      error: { message: err instanceof Error ? err.message : "Logout failed" },
    };
  }
};

export const signIn = {
  email: async ({ email, password }: { email: string; password: string }): Promise<AuthResult> => {
    try {
      const body = new URLSearchParams();
      body.set("username", email);
      body.set("password", password);
      body.set("grant_type", "password");

      const res = await fetch(authEndpoint("/auth/token"), {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          Accept: "application/json",
        },
        body,
        credentials: "include",
      });

      if (!res.ok) {
        const error = await parseError(res);
        return { data: null, error };
      }

      const data = await res.json().catch(() => ({ success: true }));
      return { data, error: null };
    } catch (err) {
      return {
        data: null,
        error: { message: err instanceof Error ? err.message : "Login failed" },
      };
    }
  },

  social: async (provider: "google" | "microsoft"): Promise<AuthResult> => {
    if (typeof window === "undefined") {
      return { data: null, error: { message: "Client-side only operation" } };
    }

    try {
      const availableProviders = await getAvailableSocialProviders();
      if (!availableProviders.includes(provider)) {
        return {
          data: null,
          error: { message: `${provider} SSO is not available right now. Please use another sign-in method.` },
        };
      }

      sessionStorage.setItem("oauth_in_progress", "true");
      sessionStorage.setItem("oauth_redirect_to", "/dashboard");

      // Build the absolute URL to the backend's SSO initiation route
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || window.location.origin;
      const url = new URL("/api/v1/auth/sso/start", baseUrl);
      url.searchParams.set("provider", provider);
      url.searchParams.set("redirect_to", "/dashboard");

      // Redirect the entire page to the backend to start the OAuth handshake
      window.location.assign(url.toString());

      return { data: { redirecting: true }, error: null };
    } catch (err) {
      return {
        data: null,
        error: { message: err instanceof Error ? err.message : "Failed to initiate social login" },
      };
    }
  },

  magicLink: async ({ email }: { email: string }): Promise<AuthResult> => {
    try {
      const url = new URL(authEndpoint("/auth/passwordless/request"), typeof window !== "undefined" ? window.location.origin : "http://localhost:3000");
      url.searchParams.set("email", email);

      const fetchUrl = API_BASE_URL ? url.toString() : `${url.pathname}${url.search}`;
      const res = await fetch(fetchUrl, {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      });

      if (!res.ok) {
        const error = await parseError(res);
        return { data: null, error };
      }

      return { data: await res.json().catch(() => ({ success: true })), error: null };
    } catch (err) {
      return {
        data: null,
        error: { message: err instanceof Error ? err.message : "Magic link request failed" },
      };
    }
  },

  zoom: async (): Promise<AuthResult> => {
    return {
      data: null,
      error: { message: "Zoom OAuth is disabled in simplified auth mode." },
    };
  },

  sso: async (): Promise<AuthResult> => {
    return {
      data: null,
      error: { message: "SSO is disabled in simplified auth mode." },
    };
  },

  passkey: async (): Promise<AuthResult> => {
    return {
      data: null,
      error: { message: "Passkey sign-in is not available." },
    };
  },
};

export const signUp = async (
  email: string,
  password: string,
  name: string,
  timezone?: string
): Promise<AuthResult> => {
  try {
    const res = await fetch(authEndpoint("/auth/register"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        email,
        password,
        full_name: name,
        timezone,
      }),
      credentials: "include",
    });

    if (!res.ok) {
      const error = await parseError(res);
      return { data: null, error };
    }

    return { data: await res.json().catch(() => ({ success: true })), error: null };
  } catch (err) {
    return {
      data: null,
      error: { message: err instanceof Error ? err.message : "Registration failed" },
    };
  }
};
