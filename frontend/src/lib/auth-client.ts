import { API_BASE_URL } from "@/lib/api";

const STORAGE_ACCESS_TOKEN = "graftai_access_token";

function getStoredAccessToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(STORAGE_ACCESS_TOKEN);
}

export function getToken() {
  return getStoredAccessToken();
}

function setStoredAccessToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem(STORAGE_ACCESS_TOKEN, token);
  } else {
    localStorage.removeItem(STORAGE_ACCESS_TOKEN);
  }
}

async function parseJsonResponse(response: Response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export const getSessionSafe = async () => {
  const checkSession = async () => {
    const headers: Record<string, string> = {};
    const localToken = getStoredAccessToken();
    if (localToken) {
      headers["Authorization"] = `Bearer ${localToken}`;
    }

    return await fetch(`${API_BASE_URL}/auth/check`, {
      method: "GET",
      credentials: "include",
      headers,
    });
  };

  const refreshSession = async () => {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    
    // Store the new token if refresh was successful
    if (response.ok) {
      const refreshData = await response.json().catch(() => null);
      if (refreshData?.access_token) {
        setStoredAccessToken(refreshData.access_token);
      }
    }
    
    return response;
  };

  try {
    let response = await checkSession();

    if (response.status === 401 || response.status === 403) {
      const refreshRes = await refreshSession();

      if (refreshRes.ok) {
        response = await checkSession();
      } else {
        return { data: null, error: new Error("Refresh token invalid or expired") };
      }
    }

    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        setStoredAccessToken(null);
      }
      return { data: null, error: new Error(`Status ${response.status}`) };
    }

    const data = await response.json();

    // If the response may include token details, persist it.
    if (data?.token?.access_token) {
      setStoredAccessToken(data.token.access_token);
    }

    return { data, error: null };
  } catch (err) {
    console.error("Failed to get session safely", err);

    // If network glitch, attempt a refresh then retry once
    try {
      const fallback = await refreshSession();
      if (fallback.ok) {
        const refreshData = await fallback.json().catch(() => null);
        if (refreshData?.access_token) {
          setStoredAccessToken(refreshData.access_token);
        }

        const retry = await checkSession();
        if (retry.ok) {
          const loadedData = await retry.json();
          return { data: loadedData, error: null };
        }
      }
    } catch (fallbackErr) {
      console.error("Refresh fallback failed", fallbackErr);
    }

    setStoredAccessToken(null);
    return { data: null, error: err };
  }
};

export const signOut = async () => {
  const response = await fetch(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to sign out");
  }

  return { success: true };
};

export const signIn = {
  email: async ({ email, password }: { email: string; password: string }) => {
    const body = new URLSearchParams();
    body.append("username", email);
    body.append("password", password);
    body.append("grant_type", "password");

    const response = await fetch(`${API_BASE_URL}/auth/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: body.toString(),
      credentials: "include",
    });

    const json = await parseJsonResponse(response);

    if (!response.ok) {
      return { error: new Error(json?.detail || "Invalid credentials") };
    }

    // Store token in localStorage for subsequent requests
    if (json?.token?.access_token) {
      setStoredAccessToken(json.token.access_token);
    }

    return { data: json, error: null };
  },

  social: async ({ provider }: { provider: "google" | "github" }) => {
    const redirect = `${API_BASE_URL}/auth/sso/start?provider=${provider}&redirect_to=/dashboard`;
    const result = await fetch(redirect, { method: "GET", credentials: "include" });
    if (!result.ok) {
      throw new Error("Social login failed");
    }
    const data = await result.json();
    if (data.authorization_url) {
      window.location.href = data.authorization_url;
      return { data, error: null };
    }
    return { error: new Error("Invalid social login response") };
  },

  magicLink: async ({ email }: { email: string }) => {
    const response = await fetch(`${API_BASE_URL}/auth/passwordless/request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
      credentials: "include",
    });

    if (!response.ok) {
      const json = await parseJsonResponse(response);
      return { error: new Error(json?.detail || "Passwordless request failed") };
    }

    return { data: await response.json(), error: null };
  },

  passkey: async ({ email }: { email?: string }) => {
    const response = await fetch(`${API_BASE_URL}/auth/fido2/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: email || "" }),
      credentials: "include",
    });

    if (!response.ok) {
      const json = await parseJsonResponse(response);
      return { error: new Error(json?.detail || "Passkey setup failed") };
    }

    return { data: await response.json(), error: null };
  },
};

export const signUp = async (email: string, password: string, name: string, timezone?: string) => {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: name, timezone }),
    credentials: "include",
  });

  if (!response.ok) {
    const json = await parseJsonResponse(response);
    return { error: new Error(json?.detail || "Registration failed") };
  }

  return { data: await response.json(), error: null };
};
