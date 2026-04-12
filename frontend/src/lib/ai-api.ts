"use client";

import { apiClient } from "./api-client";

// ═══════════════════════════════════════════════════════════════════
// TYPES - AI Automation API
// ═══════════════════════════════════════════════════════════════════

export interface AutomationStatus {
  booking_id: string;
  status: "pending" | "in_progress" | "completed" | "partial" | "failed";
  progress: number;
  current_phase?: string;
  started_at?: string;
  updated_at?: string;
  phases?: {
    id: string;
    status: "pending" | "in_progress" | "completed" | "failed";
    duration_ms?: number;
    error?: string;
  }[];
}

export interface AutomationResult {
  booking_id: string;
  status: "completed" | "partial" | "failed";
  decision_score: number;
  risk_assessment: string;
  actions: {
    tool_name: string;
    priority: string;
    parameters: Record<string, unknown>;
  }[];
  external_ids: {
    email_id?: string;
    calendar_id?: string;
    task_id?: string;
  };
  execution_time_ms: number;
  timestamp: string;
  error?: string;
}

export interface CreateBookingRequest {
  user_id: string;
  title: string;
  start_time: string;
  duration_minutes: number;
  attendee_email: string;
  attendee_name?: string;
  attendee_phone?: string;
  description?: string;
  location?: string;
  timezone?: string;
  booking_type?: string;
}

export interface CreateBookingResponse {
  id: string;
  user_id: string;
  title: string;
  start_time: string;
  duration_minutes: number;
  attendee_email: string;
  status: string;
  automation_status?: string;
  created_at: string;
}

export interface DashboardMetrics {
  total_bookings: number;
  total_automations: number;
  success_rate: number;
  avg_execution_time_ms: number;
  pending_automations: number;
  failed_automations: number;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  recent_activity: {
    id: string;
    booking_id: string;
    status: string;
    decision_score: number;
    risk_assessment: string;
    created_at: string;
  }[];
}

export interface MonitoringStats {
  automations: {
    total_today: number;
    success_rate: number;
    avg_duration_ms: number;
  };
  tools: {
    name: string;
    calls: number;
    errors: number;
    avg_duration_ms: number;
  }[];
  errors: {
    type: string;
    count: number;
    last_occurrence: string;
  }[];
}

export interface AIChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  metadata?: {
    agent_executed?: boolean;
    agent_type?: string;
    intent?: string;
    phases?: {
      id: string;
      name: string;
      status: string;
      duration_ms?: number;
    }[];
    tool_calls?: {
      tool_name: string;
      parameters: Record<string, unknown>;
      result?: unknown;
    }[];
  };
}

export interface AIChatRequest {
  message: string;
  conversation_id?: string;
  context?: {
    current_booking_id?: string;
    current_view?: string;
    user_preferences?: Record<string, unknown>;
  };
}

export interface AIChatResponse {
  id: string;
  role: string;
  content: string;
  timestamp: string;
  conversation_id: string;
  agent_executed: boolean;
  agent_type?: string;
  intent?: string;
  confidence?: number;
  phases?: Record<string, {
    status: string;
    duration_ms?: number;
    time_ms?: number;
  }>;
  entities?: Record<string, unknown>;
}

// ═══════════════════════════════════════════════════════════════════
// AI AUTOMATION API
// ═══════════════════════════════════════════════════════════════════

export const aiAutomationApi = {
  // Bookings
  async createBooking(data: CreateBookingRequest): Promise<CreateBookingResponse> {
    return apiClient.post<CreateBookingResponse>("/bookings", data);
  },

  async getBooking(id: string): Promise<CreateBookingResponse> {
    return apiClient.get<CreateBookingResponse>(`/bookings/${id}`);
  },

  // Automation Status
  async getAutomationStatus(bookingId: string): Promise<AutomationStatus> {
    return apiClient.get<AutomationStatus>(`/bookings/${bookingId}/automation-status`);
  },

  async getAutomationResult(bookingId: string): Promise<AutomationResult> {
    return apiClient.get<AutomationResult>(`/bookings/${bookingId}/automation-result`);
  },

  async retryAutomation(bookingId: string): Promise<AutomationResult> {
    return apiClient.post<AutomationResult>(`/bookings/${bookingId}/retry-automation`);
  },

  async getAutomationQueue(): Promise<{
    running: AutomationStatus[];
    pending: AutomationStatus[];
    completed_today: number;
  }> {
    return apiClient.get("/bookings/automation-queue");
  },

  // Dashboard & Metrics
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return apiClient.get<DashboardMetrics>("/monitoring/dashboard");
  },

  async getMonitoringStats(): Promise<MonitoringStats> {
    return apiClient.get<MonitoringStats>("/monitoring/stats");
  },

  async getRecentAutomations(limit: number = 10): Promise<AutomationStatus[]> {
    return apiClient.get<AutomationStatus[]>("/monitoring/automations/recent", {
      params: { limit },
    });
  },

  // AI Chat
  async sendChatMessage(data: AIChatRequest): Promise<AIChatResponse> {
    return apiClient.post<AIChatResponse>("/ai/chat", data);
  },

  async getChatHistory(conversationId: string): Promise<AIChatMessage[]> {
    return apiClient.get<AIChatMessage[]>(`/ai/chat/${conversationId}/history`);
  },

  // Health Check
  async healthCheck(): Promise<{
    status: string;
    timestamp: string;
    version: string;
    services: {
      database: boolean;
      redis?: boolean;
      ai_agent: boolean;
    };
  }> {
    return apiClient.get("/health");
  },
};

// ═══════════════════════════════════════════════════════════════════
// WEBSOCKET CLIENT
// ═══════════════════════════════════════════════════════════════════

export interface NotificationMessage {
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
}

export interface WebSocketCallbacks {
  onAutomationUpdate?: (status: AutomationStatus) => void;
  onMetricsUpdate?: (metrics: DashboardMetrics) => void;
  onNotification?: (notification: NotificationMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private callbacks: WebSocketCallbacks = {};
  private pingInterval: NodeJS.Timeout | null = null;

  constructor(private url: string) {}

  connect(callbacks: WebSocketCallbacks): void {
    this.callbacks = callbacks;
    
    try {
      // Convert http/https to ws/wss
      const wsUrl = this.url.replace(/^https?/, (protocol) =>
        protocol === "https" ? "wss" : "ws"
      );
      
      this.ws = new WebSocket(`${wsUrl}/ws`);
      
      this.ws.onopen = () => {
        console.log("WebSocket connected");
        this.reconnectAttempts = 0;
        this.callbacks.onConnect?.();
        this.startPingInterval();
      };
      
      this.ws.onmessage = (event) => {
        this.handleMessage(event.data);
      };
      
      this.ws.onclose = () => {
        console.log("WebSocket disconnected");
        this.stopPingInterval();
        this.callbacks.onDisconnect?.();
        this.attemptReconnect();
      };
      
      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.callbacks.onError?.(new Error("WebSocket connection error"));
      };
    } catch (error) {
      this.callbacks.onError?.(error as Error);
    }
  }

  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data);
      
      switch (message.type) {
        case "automation_update":
          this.callbacks.onAutomationUpdate?.(message.payload);
          break;
        case "metrics_update":
          this.callbacks.onMetricsUpdate?.(message.payload);
          break;
        case "notification":
          this.callbacks.onNotification?.(message.payload);
          break;
        case "pong":
          // Ping response received
          break;
        default:
          console.warn("Unknown WebSocket message type:", message.type);
      }
    } catch (error) {
      console.error("Failed to parse WebSocket message:", error);
    }
  }

  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000); // 30 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }
    
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect(this.callbacks);
    }, delay);
  }

  disconnect(): void {
    this.stopPingInterval();
    this.ws?.close();
    this.ws = null;
  }

  subscribeToAutomation(bookingId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "subscribe",
        channel: `automation:${bookingId}`,
      }));
    }
  }

  unsubscribeFromAutomation(bookingId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "unsubscribe",
        channel: `automation:${bookingId}`,
      }));
    }
  }
}

// ═══════════════════════════════════════════════════════════════════
// REACT HOOKS
// ═══════════════════════════════════════════════════════════════════

import { useState, useEffect, useCallback, useRef } from "react";

export function useAutomationStatus(bookingId: string | null) {
  const [status, setStatus] = useState<AutomationStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!bookingId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await aiAutomationApi.getAutomationStatus(bookingId);
      setStatus(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [bookingId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return { status, loading, error, refetch: fetchStatus };
}

export function useDashboardMetrics(pollInterval = 30000) {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      const data = await aiAutomationApi.getDashboardMetrics();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    
    if (pollInterval > 0) {
      const interval = setInterval(fetchMetrics, pollInterval);
      return () => clearInterval(interval);
    }
  }, [fetchMetrics, pollInterval]);

  return { metrics, loading, error, refetch: fetchMetrics };
}

export function useWebSocket(url?: string) {
  const [connected, setConnected] = useState(false);
  const [automationUpdate, setAutomationUpdate] = useState<AutomationStatus | null>(null);
  const [metricsUpdate, setMetricsUpdate] = useState<DashboardMetrics | null>(null);
  const [notification, setNotification] = useState<NotificationMessage | null>(null);
  const wsRef = useRef<WebSocketClient | null>(null);

  useEffect(() => {
    const wsUrl = url || process.env.NEXT_PUBLIC_WS_URL || "wss://graftai.onrender.com";
    wsRef.current = new WebSocketClient(wsUrl);
    
    wsRef.current.connect({
      onConnect: () => setConnected(true),
      onDisconnect: () => setConnected(false),
      onAutomationUpdate: setAutomationUpdate,
      onMetricsUpdate: setMetricsUpdate,
      onNotification: setNotification,
      onError: (err) => console.error("WebSocket error:", err),
    });

    return () => {
      wsRef.current?.disconnect();
    };
  }, [url]);

  const subscribeToAutomation = useCallback((bookingId: string) => {
    wsRef.current?.subscribeToAutomation(bookingId);
  }, []);

  const unsubscribeFromAutomation = useCallback((bookingId: string) => {
    wsRef.current?.unsubscribeFromAutomation(bookingId);
  }, []);

  return {
    connected,
    automationUpdate,
    metricsUpdate,
    notification,
    subscribeToAutomation,
    unsubscribeFromAutomation,
  };
}

export default aiAutomationApi;
