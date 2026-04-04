"use client";

import { useNotificationContext } from "@/providers/notification-provider";
import { NotificationType, NotificationPriority, PingStatus } from "@/types/notifications";

export const useNotification = () => {
  const { addNotification, setPingStatus, activePing, removeNotification } = useNotificationContext();

  const notify = (title: string, message?: string, type: NotificationType = "info", priority: NotificationPriority = "high") => {
    addNotification(title, { message, type, priority });
  };

  const ping = (status: PingStatus) => {
    setPingStatus(status);
  };

  return {
    notify,
    ping,
    currentPing: activePing,
    dismiss: removeNotification
  };
};
