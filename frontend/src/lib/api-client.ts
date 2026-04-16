import { getSession, signOut } from "next-auth/react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
}

class ApiClient {
  private async getHeaders(): Promise<HeadersInit> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    const session = await getSession();
    const token = (session as { accessToken?: string } | null)?.accessToken;

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

      const responseData = (await response.json()) as Record<string, unknown>;

      if (!response.ok) {
        const detail = typeof responseData.detail === "string" ? responseData.detail : undefined;
        const message = typeof responseData.message === "string" ? responseData.message : undefined;
        throw new Error(detail || message || "An API error occurred");
      }

      return responseData as T;
    } catch (error) {
      console.error(`[API Error] ${options.method || "GET"} ${endpoint}:`, error);
      throw error;
    }
  }

  public get<T>(endpoint: string, params?: Record<string, unknown>) {
    return this.request<T>(endpoint, { method: "GET", params });
  }

  public post<T>(endpoint: string, body?: unknown) {
    return this.request<T>(endpoint, { method: "POST", body: JSON.stringify(body) });
  }

  public patch<T>(endpoint: string, body?: unknown) {
    return this.request<T>(endpoint, { method: "PATCH", body: JSON.stringify(body) });
  }

  public delete<T>(endpoint: string) {
    return this.request<T>(endpoint, { method: "DELETE" });
  }
}

export const apiClient = new ApiClient();
