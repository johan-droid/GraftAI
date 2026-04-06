import { apiClient } from "./api-client";
import { getSessionSafe, invalidateSessionCache } from "./auth-client";

// Re-exporting API_BASE_URL for backward compatibility if needed
export { API_BASE_URL } from "./api-client";
export { invalidateSessionCache };

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

// ──────────────────────────────────────
// Auth: DID & Identity
// ──────────────────────────────────────
export async function didIssue() {
  return apiClient.post<{ did: string }>("/auth/did/issue");
}

export async function didVerify(did: string) {
  return apiClient.post<{ status: string }>("/auth/did/verify", { did });
}

export async function syncUserTimezone(timezone: string) {
  return apiClient.post<{ status: string; timezone: string }>("/auth/sync-timezone", { timezone });
}

export async function syncUserConsent(consents: { 
  consent_analytics?: boolean; 
  consent_notifications?: boolean; 
  consent_ai_training?: boolean 
}) {
  return apiClient.post<{ status: string }>("/auth/sync-consent", consents);
}

// ──────────────────────────────────────
// Auth: Account Deletion
// ──────────────────────────────────────
export async function deleteAccount(payload?: { reason?: string; details?: string }) {
  return apiClient.delete<{ message: string }>("/auth/account", { json: payload });
}

export async function submitLogoutFeedback(payload: { reason: string; details?: string }) {
  return apiClient.post<{ status: string }>("/auth/logout-feedback", payload);
}

export async function submitDeletionFeedback(payload: { reason: string; details?: string }) {
  return apiClient.delete<{ message: string }>("/auth/account", { json: payload });
}

export async function updateUserProfile(data: { 
  full_name?: string; 
  timezone?: string;
  bio?: string;
  job_title?: string;
  location?: string;
}) {
  return apiClient.patch<{ 
    id: string; 
    email: string; 
    full_name?: string; 
    timezone?: string;
    bio?: string;
    job_title?: string;
    location?: string;
    created_at?: string;
  }>("/users/me", data);
}

// ──────────────────────────────────────
// Auth: SSO Start
// ──────────────────────────────────────
export async function ssoStart(provider: string = "microsoft", redirectTo: string = "/dashboard") {
  return apiClient.get<{ authorization_url: string; state: string }>(
    `/auth/sso/start`, 
    { params: { provider, redirect_to: redirectTo } }
  );
}

// ──────────────────────────────────────
// Auth: Access Control
// ──────────────────────────────────────
export async function checkRole(role: string) {
  return apiClient.get<{ allowed: boolean }>("/auth/access-control/check-role", { params: { role } });
}

export async function checkAttribute(attribute: string, value: string) {
  return apiClient.get<{ allowed: boolean }>("/auth/access-control/check-attribute", { 
    params: { attribute, value } 
  });
}

// ──────────────────────────────────────
// Services: Analytics
// ──────────────────────────────────────
export async function getAnalyticsSummary(range: string = "7d") {
  return apiClient.get<{
    summary: string;
    details?: {
      meetings: number;
      hours: number;
      growth: number;
      cancellations?: number;
      recent_events?: {
        id: number;
        title: string;
        start_time: string;
        category?: string;
        is_upcoming?: boolean;
      }[];
      next_event?: {
        id: number;
        title: string;
        start_time: string;
        category?: string;
        is_upcoming?: boolean;
      } | null;
    };
  }>(
    `/analytics/summary`,
    { params: { range } }
  );
}

export interface AnalyticsRealtimeResponse {
  summary: string;
  range: string;
  generated_at: string;
  totals: {
    meetings: number;
    hours: number;
    growth: number;
    unique_attendees: number;
    cancellations: number;
  };
  series: { bucket: string; meetings: number; hours: number; categories?: Record<string, number>; dominant_category?: string | null }[];
  meeting_types: { label: string; count: number; pct: number }[];
  peak_hours: { hour: string; count: number }[];
  recent_events: {
    id: number;
    title: string;
    start_time: string;
    category?: string;
    is_upcoming?: boolean;
  }[];
  next_event?: {
    id: number;
    title: string;
    start_time: string;
    category?: string;
    is_upcoming?: boolean;
  } | null;
}

export async function getAnalyticsRealtime(range: "7d" | "30d" | "90d" = "30d") {
  return apiClient.get<AnalyticsRealtimeResponse>("/analytics/realtime", { params: { range } });
}

// ──────────────────────────────────────
// Services: AI Chat
// ──────────────────────────────────────
export async function sendAiChat(prompt: string, context?: string[], timezone?: string) {
  return apiClient.post<{ result: string; model_used?: string }>("/ai/chat", { prompt, context, timezone });
}

// ──────────────────────────────────────
// Services: Proactive Suggestions
// ──────────────────────────────────────
export async function getProactiveSuggestion(context?: string) {
  return apiClient.post<{ suggestion: string }>("/proactive/suggest", { context });
}

// ──────────────────────────────────────
// Services: Plugins
// ──────────────────────────────────────
export interface PluginItem {
  id: string;
  name: string;
  description: string;
  version: string;
  category: string;
  icon: string;
  installed: boolean;
  author?: string;
}

export async function listPlugins() {
  return apiClient.get<{ plugins: PluginItem[] }>("/plugins/list");
}

export interface IntegrationProviderStatus {
  id: "google" | "microsoft";
  connected: boolean;
  last_connected_at?: string | null;
}

export interface IntegrationStatusResponse {
  connections: Record<string, boolean>;
  providers: IntegrationProviderStatus[];
}

export async function getIntegrationStatus() {
  return apiClient.get<IntegrationStatusResponse>("/auth/integrations/status");
}

// ──────────────────────────────────────
// Notifications
// ──────────────────────────────────────
export interface NotificationItem {
  id: number;
  user_id: string;
  type: string;
  title: string;
  body?: string;
  data?: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
}

export async function getNotifications(limit: number = 25, unread_only: boolean = false) {
  return apiClient.get<NotificationItem[]>("/notifications/", { params: { limit, unread_only } });
}

export async function markNotification(id: number, is_read: boolean = true) {
  return apiClient.patch(`/notifications/${id}`, null, { params: { is_read } });
}

export async function markAllNotificationsRead() {
  return apiClient.patch(`/notifications/mark_all_read`);
}

export async function deleteNotification(id: number) {
  return apiClient.delete(`/notifications/${id}`);
}

// ──────────────────────────────────────
// Services: Consent
// ──────────────────────────────────────
export async function setConsent(consentType: string, granted: boolean) {
  return apiClient.post<{ status: string }>("/consent/set", { consent_type: consentType, granted });
}

// ──────────────────────────────────────
// Services: LLM Upgrade
// ──────────────────────────────────────
export async function upgradeLLM(modelName: string, version?: string) {
  return apiClient.post<{ status: string; details?: string }>("/upgrade/llm", { model_name: modelName, version });
}

// ──────────────────────────────────────
// Services: Calendar
// ──────────────────────────────────────
export interface CalendarEvent {
  id: number;
  user_id: string;
  title: string;
  description?: string;
  category: "meeting" | "event" | "birthday" | "task";
  color?: string;
  start_time: string;
  end_time: string;
  is_remote: boolean;
  status: string;
  meeting_platform?: string;
  meeting_link?: string;
  attendees?: string[];
  metadata_payload?: Record<string, unknown>;
  source?: string; // google, microsoft, zoom, local
  external_id?: string;
  created_at?: string;
  updated_at?: string;
}

export async function getEvents(start: string, end: string) {
  return apiClient.get<CalendarEvent[]>(`/calendar/events`, { params: { start, end } });
}

export async function createEvent(data: Partial<CalendarEvent>) {
  return apiClient.post<CalendarEvent>("/calendar/events", data);
}

export async function updateEvent(id: number, data: Partial<CalendarEvent>) {
  return apiClient.patch<CalendarEvent>(`/calendar/events/${id}`, data);
}

export async function deleteEvent(id: number) {
  return apiClient.delete<void>(`/calendar/events/${id}`);
}

// ──────────────────────────────────────
// Services: Uploads
// ──────────────────────────────────────
export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  // We bypass apiClient.post for multipart/form-data to let the browser set the boundary
  const { API_BASE_URL: BASE } = await import("./api-client");
  const { getToken } = await import("./auth-client");

  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}/api/v1/uploads`, {
    method: "POST",
    body: formData,
    headers,
    credentials: "include",
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Upload failed");
  }

  return res.json() as Promise<{ filename: string; path: string; size: number }>;
}

// ──────────────────────────────────────
// Services: Slots & Sync
// ──────────────────────────────────────
export async function getAvailableSlots(date: string, duration: number = 60, targetTimezone?: string) {
  const params: Record<string, string> = { date, duration: String(duration) };
  if (targetTimezone) params.target_timezone = targetTimezone;
  return apiClient.get<{start: string; end: string; local_label?: string; guest_label?: string}[]>(
    "/calendar/slots", 
    { params }
  );
}

export async function mfaVerify(userId: number, code: string) {
  return apiClient.post<{ status: string }>(`/auth/mfa/verify`, null, { params: { token: code } });
}

export async function manualSync() {
  return apiClient.post<{ status: string; message: string; synced_user: string }>("/calendar/sync");
}

export async function getEmailDiagnostic() {
  return apiClient.get<{
    status: string;
    message: string;
    error_type?: string;
    hint?: string;
    config_preview?: Record<string, unknown>;
  }>("/admin/email/diagnostic");
}

export async function sendTestEmail(email: string) {
  return apiClient.post<{ status: string; message: string }>("/admin/email/test", null, {
    params: { email }
  });
}
