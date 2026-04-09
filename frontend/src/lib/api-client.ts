// frontend/src/lib/api-client.ts
const rawApiBase =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://graftai.onrender.com";

const normalizedBase = rawApiBase.replace(/\/+$/, "");
const BASE_URL = normalizedBase.endsWith("/api/v1")
  ? normalizedBase
  : `${normalizedBase}/api/v1`;
export const API_BASE_URL = BASE_URL;

export interface ApiRequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | null | undefined>;
  json?: unknown;
}

export function composeEndpoint(path: string, includeBaseUrl = false) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return includeBaseUrl ? `${BASE_URL}${normalized}` : normalized;
}

export const apiClient = {
  async fetch(endpoint: string, options: ApiRequestOptions = {}) {
    const { params, json, ...requestInit } = options;
    
    // 1. Build URL with query params if provided
    let url = `${BASE_URL}${endpoint}`;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) url += `?${queryString}`;
    }

    // 2. Get the standard JWT token or legacy graftai token
    const token = typeof window !== 'undefined'
      ? localStorage.getItem("token")
        || localStorage.getItem("graftai_access_token")
        || sessionStorage.getItem("token")
        || sessionStorage.getItem("graftai_access_token")
      : null;
    
    // 3. Set up headers
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(requestInit.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    // 4. Prepare Body
    const body = json ? JSON.stringify(json) : requestInit.body;

    // 5. Make the request
    let response: Response;
    try {
      response = await fetch(url, {
        ...requestInit,
        headers,
        body,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Network request failed";
      throw new Error(`Failed to reach API at ${url}. ${message}`);
    }

    if (!response.ok) {
      if (response.status === 401) {
        if (typeof window !== 'undefined' && !window.location.pathname.includes("/login")) {
          localStorage.removeItem("token");
          window.location.href = "/login";
        }
      }
      const error = await response.json().catch(() => ({}));
      const errorMessage = typeof error.detail === 'string' ? error.detail : 
                          typeof error.message === 'string' ? error.message :
                          JSON.stringify(error.detail || error.message || error);
      throw new Error(errorMessage || `API error: ${response.status}`);
    }

    // Handle 204 No Content
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
  }
};
