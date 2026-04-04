import { getAuthToken, getToken } from "./auth-client";

function getApiBaseUrl() {
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_URL;
  if (envUrl) {
    return envUrl.replace(/\/+$|\/+$/g, "");
  }
  if (typeof window !== "undefined") {
    return ""; // relative same-origin path is preferred in browser to use /api rewrites
  }
  return "http://localhost:8000";
}

export const API_BASE_URL = getApiBaseUrl();

export function composeEndpoint(path: string, apiVersionPrefix: boolean = true): string {
  const cleanedPath = `/${path.replace(/^\/+/, "")}`;

  let effectivePath = cleanedPath;
  if (apiVersionPrefix && !cleanedPath.startsWith("/api/v1")) {
    effectivePath = `/api/v1${cleanedPath}`;
  }

  const base = API_BASE_URL.replace(/\/+$/g, "");
  return base ? `${base}${effectivePath}` : effectivePath;
}

interface RequestOptions extends RequestInit {
  timeout?: number;
  params?: Record<string, string>;
  json?: unknown;
}

class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

function isProtectedClientRoute(pathname: string): boolean {
  return pathname.startsWith("/dashboard");
}

/**
 * Hardened Fetch Wrapper with Network Timeout and Interceptor capabilities.
 */
async function request<T = unknown>(path: string, options: RequestOptions = {}): Promise<T> {
  const { timeout = 30000, params, json, ...fetchOptions } = options;

  // 1. Build URL with query params (same-origin preferred in browser)
  const apiUrl = composeEndpoint(path, true);
  const url = new URL(
    apiUrl,
    typeof window !== "undefined" ? window.location.origin : "http://localhost:8000"
  );

  if (params) {
    Object.entries(params).forEach(([key, value]) => url.searchParams.append(key, value));
  }

  const fetchUrl = API_BASE_URL ? url.toString() : url.pathname + url.search;

  // 2. Setup Network Timeout (AbortController)
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  // 3. Inject auth headers (Request Interceptor)
  const headers = new Headers(fetchOptions.headers || {});
  if (!headers.has("Content-Type") && json) {
    headers.set("Content-Type", "application/json");
  }

  let token = getToken();
  if (!token) {
    token = await getAuthToken();
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  // Double-submit CSRF header
  function getCookie(name: string): string | null {
    if (typeof document === "undefined") return null;
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(";").shift() || null;
    return null;
  }

  const xsrf = getCookie("xsrf-token");
  if (xsrf) {
    if (!headers.has("X-XSRF-TOKEN")) {
      headers.set("X-XSRF-TOKEN", xsrf);
    }
    if (!headers.has("x-xsrf-token")) {
      headers.set("x-xsrf-token", xsrf);
    }
  }

  try {
    const response = await fetch(fetchUrl, {
      ...fetchOptions,
      headers,
      body: json ? JSON.stringify(json) : fetchOptions.body,
      signal: controller.signal,
      credentials: "include",
    });

    clearTimeout(id);

    // 4. Handle Unauthorized (Response Interceptor)
    if (response.status === 401 || response.status === 403) {
      // Attempt a one-time refresh using cookie-based refresh token.
      const refreshUrl = composeEndpoint("/auth/refresh", true);
      const refreshResponse = await fetch(refreshUrl, {
        method: "POST",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      }).catch(() => null);

      if (refreshResponse?.ok) {
        const retryHeaders = new Headers(headers);
        const refreshedToken = getToken();
        if (refreshedToken) {
          retryHeaders.set("Authorization", `Bearer ${refreshedToken}`);
        } else {
          retryHeaders.delete("Authorization");
        }

        const retryResponse = await fetch(fetchUrl, {
          ...fetchOptions,
          headers: retryHeaders,
          body: json ? JSON.stringify(json) : fetchOptions.body,
          credentials: "include",
        });

        if (retryResponse.ok) {
          return retryResponse.json() as Promise<T>;
        }
      }

      // If refresh fails, only force login from protected routes.
      // Public pages may call endpoints opportunistically and should not be hard-redirected.
      if (typeof window !== "undefined") {
        const currentPath = window.location.pathname || "";
        if (isProtectedClientRoute(currentPath)) {
          window.location.assign("/login");
        }
      }
      throw new ApiError("Session expired", response.status);
    }

    // 5. General Error Handling
    if (!response.ok) {
      let errorData: unknown = {};
      let message = "Request failed";
      const rawText = await response.text().catch(() => "");

      if (rawText) {
        try {
          errorData = JSON.parse(rawText);
          if (typeof errorData === "object" && errorData !== null) {
            const data = errorData as Record<string, unknown>;
            if (data.detail) {
              message = String(data.detail);
            } else if (data.error) {
              message = String(data.error);
            } else {
              message = rawText;
            }
          } else {
            message = rawText;
          }
        } catch {
          message = rawText;
        }
      }

      const formatted = `${response.status} ${response.statusText}: ${message}`;
      throw new ApiError(formatted, response.status, errorData);
    }

    // 6. Response Parsing
    if (response.status === 204 || response.headers.get("content-length") === "0") {
      return null as unknown as T;
    }

    const text = await response.text().catch(() => "");
    if (!text) {
      return null as unknown as T;
    }

    try {
      return JSON.parse(text) as T;
    } catch {
      throw new ApiError(
        `Failed to parse JSON response: ${text.slice(0, 100)}`,
        response.status,
        text
      );
    }
  } catch (error: unknown) {
    clearTimeout(id);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(`Request timed out after ${timeout}ms`);
    }
    if (error instanceof TypeError) {
      // Network-level issue (DNS, CORS, unreachable backend)
      throw new Error(
        `Network error while calling ${url.toString()}. Ensure backend is reachable or use same-origin /api rewrites. (${error.message})`
      );
    }
    throw error;
  }
}

// Exported public API client instance
export const apiClient = {
  get: <T = unknown>(path: string, options?: RequestOptions) => 
    request<T>(path, { ...options, method: "GET" }),
    
  post: <T = unknown>(path: string, json?: unknown, options?: RequestOptions) => 
    request<T>(path, { ...options, method: "POST", json }),
    
  patch: <T = unknown>(path: string, json?: unknown, options?: RequestOptions) => 
    request<T>(path, { ...options, method: "PATCH", json }),
    
  delete: <T = unknown>(path: string, options?: RequestOptions) => 
    request<T>(path, { ...options, method: "DELETE" }),
    
  put: <T = unknown>(path: string, json?: unknown, options?: RequestOptions) => 
    request<T>(path, { ...options, method: "PUT", json }),
};
