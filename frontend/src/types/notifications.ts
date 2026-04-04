export type NotificationType = "success" | "error" | "info" | "warning";

export type NotificationPriority = "high" | "low";

export interface Notification {
  id: string;
  title: string;
  message?: string;
  type: NotificationType;
  priority: NotificationPriority;
  duration?: number; // ms
  createdAt: Date;
  context?: Record<string, any>;
}

export type PingStatus = "idle" | "syncing" | "completed" | "error";

export interface NotificationState {
  notifications: Notification[];
  activePing: PingStatus;
}
