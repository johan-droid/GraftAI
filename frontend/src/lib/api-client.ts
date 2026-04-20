import { getSession, signOut } from "next-auth/react";
import { toast } from "@/components/ui/Toast";

// Normalize API base URL so frontend endpoint calls (which use paths like
// "/analytics/summary") target the backend API prefix `/api/v1` even when
// the environment variable is set to just the host (e.g. `http://localhost:8000`).
const _rawBase = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const _trimmed = _rawBase.replace(/\/+$/g, "");
export const API_BASE_URL = _trimmed.endsWith("/api/v1") ? _trimmed : `${_trimmed}/api/v1`;

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

  public async getAuthHeaders(): Promise<HeadersInit> {
    return this.getHeaders();
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
    const maxRetries = 3;
    let retries = 0;

    const url = this.buildUrl(endpoint, params);
    while (true) {
      try {
        const headers = await this.getHeaders();
        const config: RequestInit = {
          ...customConfig,
          headers: {
            ...headers,
            ...customConfig.headers,
          },
        };

        const response = await fetch(url, config);

        if (response.status === 401) {
          if (typeof window !== "undefined") {
            await signOut({ callbackUrl: "/login" });
          }
          throw new Error("Unauthorized - Session Expired");
        }

        const isServerError = response.status >= 500 && response.status < 600;

        if (isServerError && retries < maxRetries) {
            retries++;
            // Exponential backoff: 500ms, 1000ms, 2000ms
            const delay = 500 * Math.pow(2, retries - 1);
            console.warn(`[API] Server error (${response.status}) on ${endpoint}, retrying in ${delay}ms... (Attempt ${retries}/${maxRetries})`);
            await new Promise(resolve => setTimeout(resolve, delay));
            continue;
        }

        const responseText = await response.text();
        const responseData = this.parseJsonSafe(responseText);

        if (!response.ok) {
          if (response.status === 429) {
            toast.info("Rate limit reached. Retrying in the background.");
          } else if (response.status === 503 || response.status === 502) {
            toast.info("The service is busy right now. We are retrying automatically.");
          }

          const error = typeof responseData.error === "string" ? responseData.error : undefined;
          const message = typeof responseData.message === "string" ? responseData.message : undefined;
          const statusText = response.statusText || `Request failed with status ${response.status}`;

          // Try to extract useful detail information
          let detailMsg: string | undefined;
          if (responseData) {
            if (typeof responseData.detail === "string") {
              detailMsg = responseData.detail;
            } else if (Array.isArray(responseData.detail)) {
              try {
                const msgs = responseData.detail.map((d: any) => {
                  if (typeof d === "string") return d;
                  if (d && typeof d.msg === "string") return d.msg;
                  return JSON.stringify(d);
                });
                detailMsg = msgs.join("; ");
              } catch {
                detailMsg = JSON.stringify(responseData.detail);
              }
            } else if (Array.isArray(responseData.details)) {
              detailMsg = responseData.details.join("; ");
            }
          }

          const finalMsg = error || detailMsg || message || statusText;
          console.error("[API] Bad response body:", responseData);
          throw new Error(String(finalMsg));
        }

        return responseData as T;
      } catch (error) {
        // Handle network/connection errors specifically
        if (error instanceof TypeError && error.message === "Failed to fetch") {
          if (retries < maxRetries) {
              retries++;
              const delay = 500 * Math.pow(2, retries - 1);
              console.warn(`[API Network Error] Connection failed to ${url}, retrying in ${delay}ms... (Attempt ${retries}/${maxRetries})`);
              await new Promise(resolve => setTimeout(resolve, delay));
              continue;
          }

          toast.warning("Unable to reach the backend. Please check your connection.");
          console.error(`[API Network Error] Cannot connect to backend at ${API_BASE_URL}`);
          console.error(`[API Network Error] Endpoint: ${endpoint}`);
          
          // Provide helpful error message based on environment
          const isLocalhost = API_BASE_URL.includes("localhost") || API_BASE_URL.includes("127.0.0.1");
          if (isLocalhost) {
            throw new Error(
              "Cannot connect to backend server. Please ensure:\n" +
              "1. Backend is running on http://localhost:8000\n" +
              "2. Check NEXT_PUBLIC_API_BASE_URL in .env.local"
            );
          } else {
            throw new Error(
              "Cannot connect to backend server. The service may be temporarily unavailable."
            );
          }
        }
        
        // Don't retry other errors (like 400 Bad Request, 401 Unauthorized, etc)
        // just propagate them up if we haven't hit a continue condition above
        console.error(`[API Error] ${options.method || "GET"} ${endpoint}:`, error);
        throw error;
      }
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
    const maxRetries = 3;
    let retries = 0;
    const url = this.buildUrl(endpoint);

    while (true) {
      try {
        const headers = {
          ...(await this.getHeaders()),
        } as Record<string, string>;
        if (json !== undefined) {
          headers["Content-Type"] = "application/json";
          (rest as RequestInit).body = JSON.stringify(json);
        }

        const response = await fetch(url, {
          ...rest,
          headers: {
            ...headers,
            ...customHeaders,
          },
        });

        const isServerError = response.status >= 500 && response.status < 600;

        if (isServerError && retries < maxRetries) {
          retries++;
          const delay = 500 * Math.pow(2, retries - 1);
          console.warn(`[API] Server error (${response.status}) on ${endpoint}, retrying in ${delay}ms... (Attempt ${retries}/${maxRetries})`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }

        const text = await response.text();
        const data = this.parseJsonSafe(text);

        if (!response.ok) {
          const error = typeof data.error === "string" ? data.error : undefined;
          const message = typeof data.message === "string" ? data.message : undefined;
          const statusText = response.statusText || `Request failed with status ${response.status}`;

          let detailMsg: string | undefined;
          if (data) {
            if (typeof data.detail === "string") {
              detailMsg = data.detail;
            } else if (Array.isArray(data.detail)) {
              try {
                const msgs = data.detail.map((d: any) => {
                  if (typeof d === "string") return d;
                  if (d && typeof d.msg === "string") return d.msg;
                  return JSON.stringify(d);
                });
                detailMsg = msgs.join("; ");
              } catch {
                detailMsg = JSON.stringify(data.detail);
              }
            } else if (Array.isArray(data.details)) {
              detailMsg = data.details.join("; ");
            }
          }

          const finalMsg = error || detailMsg || message || statusText;
          console.error("[API] Bad response body:", data);
          throw new Error(String(finalMsg));
        }

        return (text ? (data as T) : ({} as T));
      } catch (error) {
        if (error instanceof TypeError && error.message === "Failed to fetch") {
          if (retries < maxRetries) {
            retries++;
            const delay = 500 * Math.pow(2, retries - 1);
            console.warn(`[API Network Error] Connection failed to ${url}, retrying in ${delay}ms... (Attempt ${retries}/${maxRetries})`);
            await new Promise(resolve => setTimeout(resolve, delay));
            continue;
          }
          toast.warning("Unable to reach the backend. Please check your connection.");
        }
        throw error;
      }
    }
  }
}

export const apiClient = new ApiClient();
