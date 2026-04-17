import { getSession, signOut } from "next-auth/react";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function composeEndpoint(endpoint: string, absolute = false) {
  return absolute ? `${API_BASE_URL}${endpoint}` : endpoint;
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
  json?: unknown;
}

class ApiClient {
  private parseJsonSafe(text: string): Record<string, unknown> {
    if (!text) {
      return {};
    }

    try {
      return JSON.parse(text) as Record<string, unknown>;
    } catch {
      return {};
    }
  }

  private async getHeaders(): Promise<HeadersInit> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    const session = await getSession();
    const token = (session as { backendToken?: string; accessToken?: string } | null)?.backendToken
      ?? (session as { backendToken?: string; accessToken?: string } | null)?.accessToken;

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
  }

  private buildUrl(endpoint: string, params?: Record<string, string | number | boolean>): string {
    const url = new URL(`${API_BASE_URL}${endpoint}`);
    if (params) {
      Object.keys(params).forEach((key) =>
        url.searchParams.append(key, String(params[key]))
      );
    }
    return url.toString();
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, ...customConfig } = options;

    const url = this.buildUrl(endpoint, params);
    const headers = await this.getHeaders();

    const config: RequestInit = {
      ...customConfig,
      headers: {
        ...headers,
        ...customConfig.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (response.status === 401) {
        if (typeof window !== "undefined") {
          await signOut({ callbackUrl: "/login" });
        }
        throw new Error("Unauthorized - Session Expired");
      }

      const responseText = await response.text();
      const responseData = this.parseJsonSafe(responseText);

      if (!response.ok) {
        const error = typeof responseData.error === "string" ? responseData.error : undefined;
        const detail = typeof responseData.detail === "string" ? responseData.detail : undefined;
        const message = typeof responseData.message === "string" ? responseData.message : undefined;
        const statusText = response.statusText || `Request failed with status ${response.status}`;
        throw new Error(error || detail || message || statusText);
      }

      return responseData as T;
    } catch (error) {
      console.error(`[API Error] ${options.method || "GET"} ${endpoint}:`, error);
      throw error;
    }
  }

  private isRequestOptions(value: unknown): value is RequestOptions {
    return (
      typeof value === "object" && value !== null &&
      ("method" in value || "headers" in value || "signal" in value || "body" in value || "params" in value)
    );
  }

  public get<T>(endpoint: string, options?: RequestOptions | Record<string, string | number | boolean>) {
    const requestOptions = this.isRequestOptions(options)
      ? options
      : { params: options };

    return this.request<T>(endpoint, { method: "GET", ...requestOptions });
  }

  public post<T>(endpoint: string, body?: unknown, options: RequestOptions = {}) {
    return this.request<T>(endpoint, { method: "POST", body: JSON.stringify(body), ...options });
  }

  public patch<T>(endpoint: string, body?: unknown, options: RequestOptions = {}) {
    return this.request<T>(endpoint, { method: "PATCH", body: JSON.stringify(body), ...options });
  }

  public delete<T>(endpoint: string, options: RequestOptions = {}) {
    return this.request<T>(endpoint, { method: "DELETE", ...options });
  }

  public async fetch<T = unknown>(endpoint: string, options: RequestInit & { json?: unknown } = {}): Promise<T> {
    const { json, headers: customHeaders, ...rest } = options;
    const headers = {
      ...(await this.getHeaders()),
    } as Record<string, string>;
    if (json !== undefined) {
      headers["Content-Type"] = "application/json";
      (rest as RequestInit).body = JSON.stringify(json);
    }

    const response = await fetch(this.buildUrl(endpoint), {
      ...rest,
      headers: {
        ...headers,
        ...customHeaders,
      },
    });

    const text = await response.text();
    const data = this.parseJsonSafe(text);

    if (!response.ok) {
      const error = typeof data.error === "string" ? data.error : undefined;
      const detail = typeof data.detail === "string" ? data.detail : undefined;
      const message = typeof data.message === "string" ? data.message : undefined;
      const statusText = response.statusText || `Request failed with status ${response.status}`;
      throw new Error(String(error || detail || message || statusText));
    }

    return (text ? (data as T) : ({} as T));
  }
}

export const apiClient = new ApiClient();
