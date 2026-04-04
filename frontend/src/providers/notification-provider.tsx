"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { Notification, NotificationType, NotificationPriority, PingStatus } from "@/types/notifications";

interface NotificationContextType {
  notifications: Notification[];
  activePing: PingStatus;
  addNotification: (title: string, options?: Partial<Notification>) => void;
  removeNotification: (id: string) => void;
  setPingStatus: (status: PingStatus) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider = ({ children }: { children: React.ReactNode }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [activePing, setActivePing] = useState<PingStatus>("idle");

  const addNotification = useCallback((title: string, options?: Partial<Notification>) => {
    const id = crypto.randomUUID();
    const newNotification: Notification = {
      id,
      title,
      type: options?.type || "info",
      priority: options?.priority || "high",
      createdAt: new Date(),
      duration: options?.duration || (options?.priority === "low" ? 3000 : 5000),
      ...options
    };

    setNotifications((prev) => [...prev, newNotification]);

    // Auto-dismiss logic for high-fidelity UX
    if (newNotification.duration !== Infinity) {
      setTimeout(() => {
        removeNotification(id);
      }, newNotification.duration);
    }
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const setPingStatus = useCallback((status: PingStatus) => {
    setActivePing(status);
    
    // Auto-reset ping if it was a completion pulse
    if (status === "completed" || status === "error") {
      setTimeout(() => {
        setActivePing("idle");
      }, 4000);
    }
  }, []);

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        activePing,
        addNotification,
        removeNotification,
        setPingStatus
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotificationContext = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotificationContext must be used within a NotificationProvider");
  }
  return context;
};
