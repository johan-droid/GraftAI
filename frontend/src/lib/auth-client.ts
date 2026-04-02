import { apiClient, composeEndpoint } from "@/lib/api-client";

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(";").shift() || null;
  return null;
}

export function getCsrfHeaders(): Record<string, string> {
  const token = getCookie("xsrf-token");
  return token ? { "X-XSRF-TOKEN": token } : {};
}

export function getToken(): string | null {
  return getCookie("graftai_access_token");
}

function authEndpoint(path: string, apiVersionPrefix: boolean = true): string {
  const cleanedPath = `/${path.replace(/^\/+/, "")}`;
  let effectivePath = cleanedPath;
  if (apiVersionPrefix && !cleanedPath.startsWith("/api/v1")) {
    effectivePath = `/api/v1${cleanedPath}`;
  }

  // In browser, always use same-origin paths so Next rewrites handle backend routing.
  if (typeof window !== "undefined") {
    return effectivePath;
  }

  return composeEndpoint(path, apiVersionPrefix);
}



export const getSessionSafe = async () => {
  const checkSession = async () => {
    let lastError: unknown = null;
    const attempts = 3;

    for (let i = 0; i < attempts; i++) {
      try {
        return await fetch(authEndpoint("/auth/check", true), {
          method: "GET",
          credentials: "include",
        });
      } catch (error) {
        lastError = error;
        if (i < attempts - 1) {
          await new Promise((resolve) => setTimeout(resolve, 250 * (i + 1)));
        }
      }
    }

    console.error("Session check fetch failed after retries:", lastError);
    throw lastError;
  };

  const refreshSession = async () => {
    const urlsToTry = [
      authEndpoint("/auth/refresh", true),
      authEndpoint("/auth/refresh", false),
      authEndpoint("/auth/auth/refresh", true),
    ];

    let lastErr: unknown = null;
    for (const url of urlsToTry) {
      try {
        const res = await fetch(url, {
          method: "POST",
          credentials: "include",
        });
        if (res.ok || res.status === 401 || res.status === 403) {
          return res;
        }
        console.warn("Refresh returned non-ok status", res.status, url);
        lastErr = new Error(`Refresh status ${res.status}`);
      } catch (error) {
        console.warn("Refresh attempt failed", url, error);
        lastErr = error;
      }
    }

    console.error("Session refresh fetch failed after retries:", lastErr);
    throw lastErr;
  };

  try {
    let response = await checkSession();

    if (response.status === 401 || response.status === 403) {
      const refreshRes = await refreshSession();
      if (refreshRes.ok) {
        response = await checkSession();
      } else {
        return { data: null, error: new Error("Session expired") };
      }
    }

    if (!response.ok) {
      return { data: null, error: new Error(`Status ${response.status}`) };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (err) {
    const isNetworkError = err instanceof TypeError;
    console.error(`Session failure (${isNetworkError ? "Network" : "Other"})`, err);
    return { data: null, error: err, isNetworkError };
  }
};

export const signOut = async () => {
  try {
    await apiClient.post("/auth/logout", null, { headers: getCsrfHeaders() });
    return { success: true };
  } catch (error) {
    console.error("Sign out failed:", error);
    throw new Error("Failed to sign out");
  }
};

export const signIn = {
  email: async ({ email, password }: { email: string; password: string }) => {
    const body = new URLSearchParams();
    body.append("username", email);
    body.append("password", password);
    body.append("grant_type", "password");

    try {
      const response = await fetch(authEndpoint("/auth/token", true), {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          ...getCsrfHeaders(),
        },
        body: body.toString(),
        credentials: "include",
      });

      if (!response.ok) {
        const raw = await response.text().catch(() => "");
        let message = "Invalid credentials";
        if (raw) {
          try {
            const parsed = JSON.parse(raw) as Record<string, unknown>;
            if (parsed.detail) {
              message = String(parsed.detail);
            } else if (parsed.error) {
              message = String(parsed.error);
            }
          } catch {
            message = raw;
          }
        }
        return { error: new Error(message) };
      }

      const data = await response.json().catch(() => ({}));
      return { data, error: null };
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : "Invalid credentials";
      return { error: new Error(msg) };
    }
  },

  social: async ({ provider }: { provider: "google" | "github" }) => {
    try {
      const url = new URL(authEndpoint("/auth/sso/start", true), window.location.origin);
      url.searchParams.set("provider", provider);
      url.searchParams.set("redirect_to", "/dashboard");

      const response = await fetch(`${url.pathname}${url.search}`, {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        const raw = await response.text().catch(() => "");
        throw new Error(raw || `OAuth start failed (${response.status})`);
      }

      const data = await response.json() as { authorization_url: string; redirect_to?: string };
      
      if (data.authorization_url) {
        if (typeof window !== "undefined") {
          sessionStorage.setItem("oauth_in_progress", "true");
          sessionStorage.setItem("oauth_redirect_to", data.redirect_to || "/dashboard");
          window.location.href = data.authorization_url;
        }
        return { data, error: null };
      }
      return { error: new Error("Invalid social login response") };
    } catch (error: unknown) {
      console.error("OAuth start failed:", error);
      throw error;
    }
  },

  magicLink: async ({ email }: { email: string }) => {
    try {
      const url = new URL(authEndpoint("/auth/passwordless/request", true), window.location.origin);
      url.searchParams.set("email", email);

      const response = await fetch(`${url.pathname}${url.search}`, {
        method: "POST",
        headers: {
          ...getCsrfHeaders(),
        },
        credentials: "include",
      });

      if (!response.ok) {
        const raw = await response.text().catch(() => "");
        let message = "Passwordless request failed";
        if (raw) {
          try {
            const parsed = JSON.parse(raw) as Record<string, unknown>;
            if (parsed.detail) {
              message = String(parsed.detail);
            }
          } catch {
            message = raw;
          }
        }
        return { error: new Error(message) };
      }

      const data = await response.json().catch(() => ({}));
      return { data, error: null };
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : "Passwordless request failed";
      return { error: new Error(msg) };
    }
  },

  passkey: async ({ email }: { email?: string }) => {
    void email;
    return { error: new Error("Passkey sign-in is not available on this login flow yet.") };
  },
};

export const signUp = async (email: string, password: string, name: string, timezone?: string) => {
  try {
    const data = await apiClient.post("/auth/register", 
      { email, password, full_name: name, timezone },
      { headers: getCsrfHeaders() }
    );
    return { data, error: null };
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : "Registration failed";
    return { error: new Error(msg) };
  }
};
