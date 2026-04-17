// frontend/src/types/api.ts

// ---------------------------------------------------------
// 1. Core User & Authentication
// ---------------------------------------------------------
export interface UserProfile {
  id: string;
  email: string;
  name: string;
  bio?: string;
  timezone: string;
  time_format: "12h" | "24h"; // Note: snake_case to match Python backends typically
  buffer_minutes: number;
  avatar_url?: string;
  onboarding_completed: boolean;
  role: "admin" | "member" | "owner";
}

// ---------------------------------------------------------
// 2. Scheduling & Calendar
// ---------------------------------------------------------
export interface EventType {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  duration_minutes: number;
  url_slug: string;
  active: boolean;
  color: string;
  location_type: "video" | "phone" | "in_person";
  // Advanced settings
  requires_confirmation: boolean;
  price?: number;
}

export interface Booking {
  id: string;
  event_type_id: string;
  organizer_id: string;
  attendee_name: string;
  attendee_email: string;
  start_time: string; // ISO 8601 DateTime string
  end_time: string; // ISO 8601 DateTime string
  status: "pending" | "confirmed" | "cancelled" | "rescheduled";
  meeting_url?: string;
  cancellation_reason?: string;
  created_at: string;
}

// ---------------------------------------------------------
// 3. Teams & Resources
// ---------------------------------------------------------
export interface Team {
  id: string;
  name: string;
  slug: string;
  routing_logic: "round_robin" | "collective" | "strict";
  members: TeamMember[];
}

export interface TeamMember {
  user_id: string;
  team_id: string;
  role: "admin" | "member";
}

// ---------------------------------------------------------
// 4. Workflows & Automations
// ---------------------------------------------------------
export interface AutomationRule {
  id: string;
  name: string;
  description: string | null;
  rule_type: string;
  conditions: Record<string, unknown>;
  actions: Record<string, unknown>;
  is_enabled: boolean;
  confidence_threshold: number;
  require_confirmation: boolean;
  max_executions_per_day: number | null;
  execution_count_today: number;
  priority: number;
  created_at: string;
}

// ---------------------------------------------------------
// 5. Standard API Responses
// ---------------------------------------------------------
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}

export interface ApiError {
  detail: string;
  code?: string;
  status: number;
}
