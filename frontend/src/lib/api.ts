import { apiClient } from "./api-client";

// Re-exporting API_BASE_URL for backward compatibility if needed
export { API_BASE_URL } from "./api-client";

// ──────────────────────────────────────
// Auth: Session Check
// ──────────────────────────────────────
export async function refreshSession() {
  // Verifies the current JWT by fetching the user profile
  try {
    const user = await apiClient.get("/users/me");
    return { user };
  } catch {
    throw new Error("No valid session to refresh");
  }
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
  return updateUserProfile({ timezone });
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

export async function requestMagicLink(email: string) {
  return apiClient.post<{ email: string; code?: string; expires_at?: string; message: string }>(
    "/auth/passwordless/request",
    null,
    { params: { email } }
  );
}

export async function verifyMagicLink(email: string, code: string) {
  return apiClient.post<{ access_token: string; refresh_token: string; token_type: string; expires_in: number }>(
    "/auth/passwordless/verify",
    null,
    { params: { email, code } }
  );
}

function unwrapApiData<T>(response: T | { data?: T }): T {
  if (response && typeof response === "object" && "data" in response && (response as { data?: T }).data !== undefined) {
    return (response as { data: T }).data;
  }
  return response as T;
}

export async function updateUserProfile(data: { 
  display_name?: string;
  full_name?: string; 
  username?: string;
  timezone?: string;
  bio?: string;
  phone?: string;
  time_format?: string;
  theme?: string;
  brand_color_light?: string;
  brand_color_dark?: string;
  booking_layout?: string;
  default_calendar_id?: string;
  preferences?: Record<string, any>;
}) {
  const response = await apiClient.patch<{ 
    id: string; 
    email: string; 
    username?: string; 
    full_name?: string; 
    display_name?: string;
    avatar_url?: string;
    bio?: string;
    phone?: string;
    timezone?: string;
    time_format?: string;
    theme?: string;
    brand_color_light?: string;
    brand_color_dark?: string;
    booking_layout?: string;
    default_calendar_id?: string;
    preferences?: Record<string, any>;
    onboarding_completed?: boolean;
    completed_steps?: string[];
    created_at?: string;
  }>("/users/me", data);
  return unwrapApiData(response);
}

export async function saveUserProfile(data: { 
  display_name?: string;
  full_name?: string; 
  username?: string; 
  timezone?: string;
  bio?: string;
  phone?: string;
  time_format?: string;
  theme?: string;
  brand_color_light?: string;
  brand_color_dark?: string;
  booking_layout?: string;
  default_calendar_id?: string;
  preferences?: Record<string, any>;
}) {
  const response = await apiClient.post<{ 
    success: boolean;
    message: string;
    data: {
      id: string;
      email: string;
      username?: string;
      full_name?: string;
      display_name?: string;
      avatar_url?: string;
      bio?: string;
      phone?: string;
      timezone?: string;
      time_format?: string;
      theme?: string;
      brand_color_light?: string;
      brand_color_dark?: string;
      booking_layout?: string;
      default_calendar_id?: string;
      preferences?: Record<string, any>;
      onboarding_completed?: boolean;
      completed_steps?: string[];
      created_at?: string;
    };
  }>("/users/me/profile", data);
  return unwrapApiData(response);
}

export async function uploadProfileAvatar(file: File) {
  const body = new FormData();
  body.append("file", file);
  const response = await apiClient.fetch<{
    success: boolean;
    message?: string;
    data?: { avatar_url?: string };
    avatar_url?: string;
    avatarUrl?: string;
  }>("/users/me/profile/avatar", {
    method: "POST",
    body,
  });

  return response.data?.avatar_url ?? response.avatar_url ?? response.avatarUrl ?? "";
}

export interface ProfileSetupStatus {
  completed_steps: string[];
  onboarding_completed: boolean;
  profile: {
    id: string;
    email: string;
    username?: string;
    full_name?: string;
    display_name?: string;
    avatar_url?: string;
    bio?: string;
    phone?: string;
    timezone?: string;
    time_format?: string;
    theme?: string;
    brand_color_light?: string;
    brand_color_dark?: string;
    booking_layout?: string;
    default_calendar_id?: string;
    preferences?: Record<string, any>;
    onboarding_completed?: boolean;
    completed_steps?: string[];
  };
}

export async function getProfileSetupStatus() {
  const response = await apiClient.get<ProfileSetupStatus | { success?: boolean; data?: ProfileSetupStatus }>("/users/me/profile/setup-status");
  return unwrapApiData(response);
}

export async function getGoogleCalendarAuthUrl() {
  const response = await apiClient.get<{ authUrl: string; state: string } | { success?: boolean; data?: { authUrl: string; state: string } }>("/users/me/calendars/oauth/google/auth-url");
  const data = unwrapApiData(response) as { authUrl?: string; auth_url?: string; state: string };
  return { authUrl: data.authUrl ?? data.auth_url ?? "", state: data.state };
}

export async function completeOnboardingStep(stepId: string, stepData?: Record<string, any>) {
  const response = await apiClient.post<{ success: boolean; step: string; completed_steps: string[] } | { success: boolean; data?: { completed_steps: string[]; next_step?: string | null } }>(
    `/users/me/profile/complete-step/${encodeURIComponent(stepId)}`,
    stepData || {}
  );
  return unwrapApiData(response);
}

export async function getOnboardingPreview() {
  const response = await apiClient.get<{ bookingPageUrl: string; isLive: boolean } | { success?: boolean; data?: { bookingPageUrl: string; isLive: boolean } }>("/users/me/onboarding/preview");
  return unwrapApiData(response);
}

export async function completeOnboarding() {
  const response = await apiClient.post<{ success: boolean; redirectUrl: string } | { success?: boolean; data?: { redirectUrl: string } }>("/users/me/onboarding/complete");
  const data = unwrapApiData(response) as { redirectUrl?: string; redirect_url?: string };
  return { redirectUrl: data.redirectUrl ?? data.redirect_url ?? "/dashboard" };
}

export interface ApiKeyItem {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  last_used_at?: string | null;
  revoked_at?: string | null;
  is_active: boolean;
}

export interface CreatedApiKey extends ApiKeyItem {
  token: string;
}

export async function listApiKeys() {
  return apiClient.get<{ items: ApiKeyItem[] }>("/users/me/api-keys");
}

export async function createApiKey(name?: string) {
  return apiClient.post<CreatedApiKey>("/users/me/api-keys", { name });
}

export async function revokeApiKey(keyId: string) {
  return apiClient.delete<{ status: string; id: string }>(`/users/me/api-keys/${encodeURIComponent(keyId)}`);
}

export interface OutOfOfficeBlock {
  id: string;
  start_time: string;
  end_time: string;
  reason?: string | null;
  created_at: string;
}

export async function listOutOfOfficeBlocks() {
  return apiClient.get<{ items: OutOfOfficeBlock[] }>("/users/me/out-of-office");
}

export async function createOutOfOfficeBlock(payload: {
  start_time: string;
  end_time: string;
  reason?: string;
}) {
  return apiClient.post<OutOfOfficeBlock>("/users/me/out-of-office", payload);
}

export async function deleteOutOfOfficeBlock(blockId: string) {
  return apiClient.delete<{ status: string; id: string }>(`/users/me/out-of-office/${encodeURIComponent(blockId)}`);
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
export interface AiChatActionResult {
  type: string;
  status?: string;
  [key: string]: unknown;
}

export interface AiChatServiceResponse {
  result: string;
  model_used?: string;
  action?: AiChatActionResult;
  milestone?: string;
}

export async function sendAiChat(prompt: string, context?: string[], timezone?: string) {
  return apiClient.post<AiChatServiceResponse>("/ai/chat", { prompt, context, timezone });
}

export interface AiChatStreamPhaseEvent {
  phase?: string;
  status?: string;
  detail?: string;
  [key: string]: unknown;
}

export interface AiChatStreamHandlers {
  onChunk?: (chunk: string) => void;
  onPhase?: (phase: AiChatStreamPhaseEvent) => void;
  onDone?: (response: AiChatServiceResponse) => void;
  onError?: (error: unknown) => void;
  onFunctionCall?: (payload: Record<string, unknown>) => void;
}

export async function streamAiChat(
  prompt: string,
  context?: string[],
  timezone?: string,
  handlers: AiChatStreamHandlers = {}
) {
  const controller = new AbortController();
  const headers = await apiClient.getAuthHeaders();
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;

  void (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/ai/stream`, {
        method: "POST",
        headers: {
          ...(headers as Record<string, string>),
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ prompt, context, timezone }),
        signal: controller.signal,
        credentials: "include",
      });

      if (!response.ok) {
        const errorBody = await response.text().catch(() => "");
        throw new Error(errorBody || response.statusText || `Request failed with status ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Streaming response body is unavailable");
      }

      reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let sawDone = false;

      const processBlock = (block: string) => {
        if (!block.trim()) {
          return;
        }

        const lines = block.split(/\r?\n/);
        let eventName = "message";
        const dataLines: string[] = [];

        for (const line of lines) {
          if (line.startsWith("event:")) {
            eventName = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            dataLines.push(line.slice(5).trim());
          }
        }

        const rawData = dataLines.join("\n");
        let parsed: unknown = rawData;
        if (rawData) {
          try {
            parsed = JSON.parse(rawData);
          } catch {
            parsed = rawData;
          }
        }

        if (eventName === "message") {
          const chunk = typeof parsed === "object" && parsed !== null && "chunk" in parsed && typeof (parsed as { chunk?: unknown }).chunk === "string"
            ? (parsed as { chunk: string }).chunk
            : typeof parsed === "string"
              ? parsed
              : rawData;
          if (chunk) {
            handlers.onChunk?.(chunk);
          }
          return;
        }

        if (eventName === "phase") {
          handlers.onPhase?.(parsed as AiChatStreamPhaseEvent);
          return;
        }

        if (eventName === "function_call") {
          handlers.onFunctionCall?.(parsed as Record<string, unknown>);
          return;
        }

        if (eventName === "done") {
          sawDone = true;
          handlers.onDone?.(parsed as AiChatServiceResponse);
          return;
        }

        if (eventName === "error") {
          handlers.onError?.(parsed);
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split(/\n\n/);
        for (let index = 0; index < blocks.length - 1; index += 1) {
          processBlock(blocks[index]);
        }
        buffer = blocks[blocks.length - 1];
      }

      if (buffer.trim()) {
        processBlock(buffer);
      }

      if (!sawDone) {
        handlers.onDone?.({ result: "" });
      }
    } catch (error) {
      if ((error as { name?: string }).name !== "AbortError") {
        handlers.onError?.(error);
      }
    } finally {
      reader?.releaseLock();
    }
  })();

  return controller;
}

// ──────────────────────────────────────
// Services: Proactive Suggestions
// ──────────────────────────────────────
export interface SmartAction {
  id: string;
  action_type: string;
  title: string;
  description: string;
  target_entity_id?: string;
  suggested_time?: string;
  confidence_score: number;
  payload?: Record<string, any>;
}

export interface ProactiveSuggestionResponse {
  suggestion: string;
  smart_actions?: SmartAction[];
}

export async function getProactiveSuggestion(context?: string) {
  return apiClient.post<ProactiveSuggestionResponse>("/proactive/suggest", { context });
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

export interface AuthIntegrationStatusResponse {
  connections: Record<string, boolean>;
  providers: IntegrationProviderStatus[];
}

export async function getAuthIntegrationStatus() {
  return apiClient.get<AuthIntegrationStatusResponse>("/auth/integrations/status");
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
  id: number | string;
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

export async function getEvents(start: string, end: string, options: Record<string, unknown> = {}) {
  return apiClient.get<CalendarEvent[]>(`/calendar/events`, { ...options, params: { start, end } });
}

export async function createEvent(data: Partial<CalendarEvent>) {
  return apiClient.post<CalendarEvent>("/calendar/events", data);
}

export async function updateEvent(id: number | string, data: Partial<CalendarEvent>) {
  return apiClient.patch<CalendarEvent>(`/calendar/events/${id}`, data);
}

export async function deleteEvent(id: number | string) {
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

  const headers: Record<string, string> = {};
  const token = typeof window !== 'undefined' ? localStorage.getItem("token") : null;
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

export interface PublicEventDetailsResponse {
  title: string;
  description?: string;
  duration_minutes: number;
  meeting_provider?: string;
  username: string;
  event_type_slug: string;
  timezone: string;
  recurrence_rule?: string;
  custom_questions?: Array<Record<string, unknown>>;
  requires_attendee_confirmation?: boolean;
  requires_payment?: boolean;
  payment_amount?: number;
  payment_currency?: string;
  travel_time_before_minutes?: number;
  travel_time_after_minutes?: number;
}

export interface PublicUserProfileResponse {
  username: string;
  full_name?: string;
  timezone: string;
}

export interface PublicAvailabilityResponse {
  availability: Record<string, string[]>;
}

export interface PublicBookingConfirmation {
  success: boolean;
  booking_id: string;
  event_id: string;
  organizer_start_time: string;
  organizer_end_time: string;
  invitee_start_time: string;
  invitee_end_time: string;
  invitee_zone: string;
  meeting_url?: string;
  action_token?: string;
  manage_url?: string;
  reschedule_url?: string;
  cancel_url?: string;
}

export interface PublicAvailabilitySlot {
  start: string;
  end: string;
  organizer_start: string;
  organizer_end: string;
  invitee_start: string;
  invitee_end: string;
  invitee_zone: string;
}

export interface PublicDailyAvailabilityResponse {
  date: string;
  slots: PublicAvailabilitySlot[];
}

export interface PublicBookingActionResponse {
  success: boolean;
  booking_id: string;
  status: string;
  message: string;
  organizer_start_time?: string;
  organizer_end_time?: string;
  invitee_start_time?: string;
  invitee_end_time?: string;
  invitee_zone?: string;
}

export interface PublicBookingDetailsResponse {
  booking_id: string;
  status: string;
  full_name: string;
  email: string;
  event_title: string;
  organizer_name: string;
  organizer_username: string;
  organizer_timezone: string;
  event_type_slug?: string;
  duration_minutes: number;
  organizer_start_time: string;
  organizer_end_time: string;
  invitee_start_time: string;
  invitee_end_time: string;
  invitee_zone: string;
  meeting_url?: string;
  action_token: string;
  reschedule_url: string;
  cancel_url: string;
}

export async function getPublicEventDetails(username: string, eventType: string) {
  return apiClient.get<PublicEventDetailsResponse>(
    `/public/events/${encodeURIComponent(username)}/${encodeURIComponent(eventType)}`
  );
}

export async function getPublicUserProfile(username: string) {
  return apiClient.get<PublicUserProfileResponse>(
    `/public/users/${encodeURIComponent(username)}`
  );
}

export async function getPublicEventAvailability(
  username: string,
  eventType: string,
  month: string,
  timeZone?: string
) {
  const params: Record<string, string> = { month };
  if (timeZone) params.time_zone = timeZone;
  return apiClient.get<PublicAvailabilityResponse>(
    `/public/events/${encodeURIComponent(username)}/${encodeURIComponent(eventType)}/availability`,
    { params }
  );
}

export async function getPublicEventAvailabilityByDate(
  username: string,
  eventType: string,
  date: string,
  timeZone?: string
) {
  const params: Record<string, string> = { date };
  if (timeZone) params.time_zone = timeZone;
  return apiClient.get<PublicDailyAvailabilityResponse>(
    `/public/users/${encodeURIComponent(username)}/${encodeURIComponent(eventType)}/availability`,
    { params }
  );
}

export interface EventTypePayload {
  name: string;
  description?: string;
  slug?: string;
  color?: string;
  duration_minutes?: number;
  meeting_provider?: string;
  is_public?: boolean;
  buffer_before_minutes?: number | null;
  buffer_after_minutes?: number | null;
  minimum_notice_minutes?: number | null;
  availability?: Record<string, string[]>;
  exceptions?: unknown[];
  recurrence_rule?: string | null;
  custom_questions?: Array<Record<string, unknown>> | null;
  requires_attendee_confirmation?: boolean;
  travel_time_before_minutes?: number;
  travel_time_after_minutes?: number;
  requires_payment?: boolean;
  payment_amount?: number | null;
  payment_currency?: string;
  team_assignment_method?: string;
}

export interface EventTypeResponse extends EventTypePayload {
  id: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export async function listEventTypes() {
  return apiClient.get<EventTypeResponse[]>("/event-types");
}

export async function createEventType(payload: EventTypePayload) {
  return apiClient.post<EventTypeResponse>("/event-types", payload);
}

export async function updateEventType(eventTypeId: string, payload: Partial<EventTypePayload>) {
  return apiClient.patch<EventTypeResponse>(`/event-types/${encodeURIComponent(eventTypeId)}`, payload);
}

export async function deleteEventType(eventTypeId: string) {
  return apiClient.delete<{ status: string }>(`/event-types/${encodeURIComponent(eventTypeId)}`);
}

export interface PublicPaymentIntentResponse {
  payment_intent_id: string;
  amount: number;
  currency: string;
  status: string;
  client_secret?: string;
}

export interface PublicPaymentConfirmationResponse {
  success: boolean;
  payment_intent_id: string;
  payment_status: string;
}

export interface TeamMemberResponse {
  id: string;
  user_id: string;
  username?: string;
  assignment_method: string;
  priority: number;
  created_at: string;
  updated_at: string;
}

export async function getEventTypeTeamMembers(eventTypeId: string) {
  return apiClient.get<TeamMemberResponse[]>(`/event-types/${encodeURIComponent(eventTypeId)}/team-members`);
}

export async function addEventTypeTeamMember(eventTypeId: string, payload: { username: string; assignment_method?: string; priority?: number }) {
  return apiClient.post<TeamMemberResponse>(`/event-types/${encodeURIComponent(eventTypeId)}/team-members`, payload);
}

export async function updateEventTypeTeamMember(eventTypeId: string, memberId: string, payload: { assignment_method?: string; priority?: number }) {
  return apiClient.patch<TeamMemberResponse>(`/event-types/${encodeURIComponent(eventTypeId)}/team-members/${encodeURIComponent(memberId)}`, payload);
}

export async function deleteEventTypeTeamMember(eventTypeId: string, memberId: string) {
  return apiClient.delete<{ status: string }>(`/event-types/${encodeURIComponent(eventTypeId)}/team-members/${encodeURIComponent(memberId)}`);
}

export async function createPublicPaymentIntent(username: string, eventType: string) {
  return apiClient.post<PublicPaymentIntentResponse>(
    `/public/events/${encodeURIComponent(username)}/${encodeURIComponent(eventType)}/payment-intent`,
    null
  );
}

export async function confirmPublicPaymentIntent(username: string, eventType: string, payload: { payment_intent_id: string; payment_method?: string }) {
  return apiClient.post<PublicPaymentConfirmationResponse>(
    `/public/events/${encodeURIComponent(username)}/${encodeURIComponent(eventType)}/payment-intent/confirm`,
    payload
  );
}

export async function bookPublicEvent(
  username: string,
  eventType: string,
  payload: {
    full_name: string;
    email: string;
    start_time: string;
    end_time: string;
    time_zone?: string;
    questions?: Record<string, unknown>;
    metadata?: Record<string, unknown>;
  }
) {
  return apiClient.post<PublicBookingConfirmation>(
    `/public/events/${encodeURIComponent(username)}/${encodeURIComponent(eventType)}/book`,
    payload
  );
}

export async function reschedulePublicBooking(
  bookingId: string,
  token: string,
  payload: { new_start_time: string; time_zone?: string }
) {
  return apiClient.patch<PublicBookingActionResponse>(
    `/public/bookings/${encodeURIComponent(bookingId)}/reschedule`,
    payload,
    { params: { token } }
  );
}

export async function getPublicBookingDetails(bookingId: string, token: string) {
  return apiClient.get<PublicBookingDetailsResponse>(
    `/public/bookings/${encodeURIComponent(bookingId)}`,
    { params: { token } }
  );
}

export async function cancelPublicBooking(bookingId: string, token: string, reason?: string) {
  return apiClient.delete<PublicBookingActionResponse>(
    `/public/bookings/${encodeURIComponent(bookingId)}`,
    { params: { token }, json: reason ? { reason } : undefined }
  );
}

export async function mfaVerify(userId: number, code: string) {
  return apiClient.post<{ status: string }>(`/auth/mfa/verify`, null, { params: { token: code } });
}

export async function manualSync() {
  return apiClient.post<{ status: string; message: string; synced_providers?: string[] }>("/calendar/sync");
}

export interface IntegrationsStatusResponse {
  active_providers: string[];
  inactive_providers: string[];
}

export async function getIntegrationStatus() {
  return apiClient.get<IntegrationsStatusResponse>("/users/me/integrations");
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
