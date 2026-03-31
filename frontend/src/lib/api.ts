const windowOrigin = (typeof window !== "undefined" && window.location.origin) || "";
const defaultHost = windowOrigin ? windowOrigin.replace(/:300\d/, ":8000") : "http://localhost:8000";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "";

if (typeof window !== "undefined") {
  console.debug("API_BASE_URL set to", API_BASE_URL);
  if (
    process.env.NODE_ENV === "production" &&
    (API_BASE_URL.startsWith("http://localhost") || API_BASE_URL.startsWith("http://127.0.0.1"))
  ) {
    console.warn(
      "Running in production with localhost backend URL. Please set NEXT_PUBLIC_API_BASE_URL or NEXT_PUBLIC_BACKEND_URL to your deployed backend domain."
    );
  }
}

import { getSessionSafe, getToken } from "@/lib/auth-client";

interface ApiOptions {
  method?: string;
  body?: Record<string, unknown> | null;
}

async function resolveUnauthorized() {
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

async function apiFetch<T = unknown>(path: string, options: ApiOptions = {}) {
  const { method = "GET", body } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Rely on HttpOnly cookie for auth fallback - credentials: "include" sends cookies automatically
  // The backend reads 'graftai_access_token' cookie via get_current_user()

  const res = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include", // HttpOnly cookies are sent automatically
  });

  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      // Attempt to refresh the session transparently before redirecting
      const { data, error: refreshError } = await getSessionSafe();
      if (data && !refreshError) {
        // Retry the request once with the new token
        const retryRes = await fetch(`${API_BASE_URL}/api/v1${path}`, {
          method,
          headers: {
            ...headers,
            "Authorization": `Bearer ${getToken()}`
          },
          body: body ? JSON.stringify(body) : undefined,
          credentials: "include",
        });

        if (retryRes.ok) {
          return retryRes.json() as Promise<T>;
        }
      }

      await resolveUnauthorized();
      throw new Error("Unauthorized");
    }

    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${res.status}`);
  }

  return res.json() as Promise<T>;
}

// ──────────────────────────────────────
// Auth: Session Check
// ──────────────────────────────────────
export async function refreshSession() {
  const session = await getSessionSafe();
  if (!session?.data?.session) {
    throw new Error("No session to refresh");
  }
  return session.data;
}
// Backend: POST /auth/did/verify  (Pydantic body: {user_id, did})
// ──────────────────────────────────────
export async function didIssue() {
  return apiFetch<{ did: string }>(
    "/auth/did/issue",
    { method: "POST" }
  );
}

export async function didVerify(did: string) {
  return apiFetch<{ status: string }>("/auth/did/verify", {
    method: "POST",
    body: { did },
  });
}

export async function syncUserTimezone(timezone: string) {
  return apiFetch<{ status: string; timezone: string }>("/auth/sync-timezone", {
    method: "POST",
    body: { timezone },
  });
}

export async function syncUserConsent(consents: { 
  consent_analytics?: boolean; 
  consent_notifications?: boolean; 
  consent_ai_training?: boolean 
}) {
  return apiFetch<{ status: string }>("/auth/sync-consent", {
    method: "POST",
    body: consents,
  });
}

// ──────────────────────────────────────
// Auth: Account Deletion
// Backend: DELETE /auth/account
// ──────────────────────────────────────
export async function deleteAccount() {
  return apiFetch<{ message: string }>("/auth/account", {
    method: "DELETE",
  });
}

// ──────────────────────────────────────
// Auth: SSO Start
// Backend: GET /auth/sso/start?provider=...&redirect_to=...
// ──────────────────────────────────────
export async function ssoStart(provider: string = "github", redirectTo: string = "/dashboard") {
  return apiFetch<{ authorization_url: string; state: string }>(
    `/auth/sso/start?provider=${provider}&redirect_to=${encodeURIComponent(redirectTo)}`
  );
}

// ──────────────────────────────────────
// Auth: Access Control
// Backend: GET /auth/access-control/check-role?user_id=...&role=...
// Backend: GET /auth/access-control/check-attribute?user_id=...&attribute=...&value=...
// ──────────────────────────────────────
export async function checkRole(role: string) {
  return apiFetch<{ allowed: boolean }>(
    "/auth/access-control/check-role?" + new URLSearchParams({ role })
  );
}

export async function checkAttribute(attribute: string, value: string) {
  return apiFetch<{ allowed: boolean }>(
    "/auth/access-control/check-attribute?" + new URLSearchParams({ attribute, value })
  );
}

// ──────────────────────────────────────
// Services: Analytics
// Backend: POST /analytics/summary  (Pydantic body)
// ──────────────────────────────────────
export async function getAnalyticsSummary(range: string = "7d") {
  return apiFetch<{ summary: string; details?: { meetings: number; hours: number; growth: number } }>(
    `/analytics/summary?range=${encodeURIComponent(range)}`, 
    { method: "GET" }
  );
}

// ──────────────────────────────────────
// Services: AI Chat
// Backend: POST /ai/chat  (Pydantic body)
// ──────────────────────────────────────
export async function sendAiChat(prompt: string, context?: string[], timezone?: string) {
  return apiFetch<{ result: string; model_used?: string }>("/ai/chat", {
    method: "POST",
    body: { prompt, context, timezone },
  });
}

// ──────────────────────────────────────
// Services: Proactive Suggestions
// Backend: POST /proactive/suggest  (Pydantic body)
// ──────────────────────────────────────
export async function getProactiveSuggestion(context?: string) {
  return apiFetch<{ suggestion: string }>("/proactive/suggest", {
    method: "POST",
    body: { context },
  });
}

// ──────────────────────────────────────
// Services: Plugins
// Backend: GET /plugins/list
// ──────────────────────────────────────
export async function listPlugins() {
  return apiFetch<{ plugins: { name: string; description: string; version: string; author?: string }[] }>("/plugins/list");
}

// ──────────────────────────────────────
// Services: Consent
// Backend: POST /consent/set  (Pydantic body)
// ──────────────────────────────────────
export async function setConsent(consentType: string, granted: boolean) {
  return apiFetch<{ status: string }>("/consent/set", {
    method: "POST",
    body: { consent_type: consentType, granted },
  });
}

// ──────────────────────────────────────
// Services: LLM Upgrade
// Backend: POST /upgrade/llm  (Pydantic body)
// ──────────────────────────────────────
export async function upgradeLLM(modelName: string, version?: string) {
  return apiFetch<{ status: string; details?: string }>("/upgrade/llm", {
    method: "POST",
    body: { model_name: modelName, version },
  });
}

// ──────────────────────────────────────
// Services: Calendar
// Backend: GET /calendar/events
// Backend: POST /calendar/events
// Backend: PATCH /calendar/events/{id}
// Backend: DELETE /calendar/events/{id}
// Backend: GET /calendar/slots
// ──────────────────────────────────────
export interface CalendarEvent {
  id: number;
  user_id: number;
  title: string;
  description?: string;
  category: "meeting" | "event" | "birthday" | "task";
  color?: string;
  start_time: string;
  end_time: string;
  is_remote: boolean;
  status: string;
  metadata_payload?: Record<string, unknown>;
  source?: string; // google, microsoft, zoom, local
  external_id?: string;
  created_at?: string;
  updated_at?: string;
}

export async function getEvents(start: string, end: string) {
  return apiFetch<CalendarEvent[]>(`/calendar/events?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
}

export async function createEvent(data: Partial<CalendarEvent>) {
  return apiFetch<CalendarEvent>("/calendar/events", {
    method: "POST",
    body: data as Record<string, unknown>,
  });
}

export async function updateEvent(id: number, data: Partial<CalendarEvent>) {
  return apiFetch<CalendarEvent>(`/calendar/events/${id}`, {
    method: "PATCH",
    body: data as Record<string, unknown>,
  });
}

export async function deleteEvent(id: number) {
  // Use apiFetch for consistency and token injection
  return apiFetch<{ status: string }>(`/calendar/events/${id}`, {
    method: "DELETE",
  });
}

export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  // Rely on HttpOnly cookie - no manual token injection needed
  const res = await fetch(`${API_BASE_URL}/api/v1/uploads`, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Upload failed");
  }

  return res.json() as Promise<{ filename: string; path: string; size: number }>;
}

export async function getAvailableSlots(date: string, duration: number = 60, targetTimezone?: string) {
  let url = `/calendar/slots?date=${encodeURIComponent(date)}&duration=${duration}`;
  if (targetTimezone) {
    url += `&target_timezone=${encodeURIComponent(targetTimezone)}`;
  }
  return apiFetch<{start: string; end: string; local_label?: string; guest_label?: string}[]>(url);
}

export async function mfaVerify(userId: number, code: string) {
  return apiFetch<{ status: string }>(`/auth/mfa/verify?token=${encodeURIComponent(code)}`, {
    method: "POST"
  });
}

export async function manualSync() {
  return apiFetch<{ status: string; synced_count: number }>("/calendar/sync", {
    method: "POST"
  });
}
