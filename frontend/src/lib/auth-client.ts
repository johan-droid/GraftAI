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

export function getToken(): string | null {
  if (typeof document === "undefined") return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; graftai_access_token=`);
  const token = parts.length === 2 ? parts.pop()?.split(";").shift() || null : null;
  if (token) return token;

  try {
    if (typeof window !== "undefined" && window.sessionStorage) {
      return window.sessionStorage.getItem("graftai_access_token");
    }
  } catch {
    // Ignore storage access issues.
  }

  return null;
}

export async function getAuthToken(): Promise<string | null> {
  const now = Date.now();
  if (_cachedToken && now < _cacheExpiry) {
    return _cachedToken;
  }

  try {
    const session = await getSessionSafe();
    const token = session?.data?.session?.token ?? null;
    _cachedToken = token;
    _cacheExpiry = now + SESSION_CACHE_TTL_MS;
    return token;
  } catch {
    return null;
  }
}

export function invalidateSessionCache(): void {
  _cachedToken = null;
  _cacheExpiry = 0;
}

export function getCsrfHeaders(): Record<string, string> {
  if (typeof document === "undefined") return {};
  const value = `; ${document.cookie}`;
  const parts = value.split(`; xsrf-token=`);
  const token = parts.length === 2 ? parts.pop()?.split(";").shift() || null : null;
  if (!token) return {};
  // Keep compatibility with both header casings in backend and proxies.
  return {
    "X-XSRF-TOKEN": token,
    "x-xsrf-token": token,
  };
}

export const getSessionSafe = async () => {
  try {
    const headers: Record<string, string> = {
      Accept: "application/json",
    };

    const token = getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const res = await fetch(authEndpoint("/auth/check"), {
      method: "GET",
      credentials: "include",
      headers,
    });

    if (!res.ok) {
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
