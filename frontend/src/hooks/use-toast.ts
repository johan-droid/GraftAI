"use client";

import { useState, useCallback, useEffect } from "react";

export type ToastType = "success" | "error" | "info" | "warning";

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

let toastListeners: ((toasts: Toast[]) => void)[] = [];
let toastQueue: Toast[] = [];

function notify(listeners: ((toasts: Toast[]) => void)[], toasts: Toast[]) {
  listeners.forEach((fn) => fn([...toasts]));
}

export const toast = {
  show(message: string, type: ToastType = "info", duration = 3500) {
    const id = Math.random().toString(36).slice(2);
    const newToast: Toast = { id, message, type, duration };
    toastQueue = [...toastQueue, newToast];
    notify(toastListeners, toastQueue);
    setTimeout(() => {
      toastQueue = toastQueue.filter((t) => t.id !== id);
      notify(toastListeners, toastQueue);
    }, duration);
  },
  success(message: string, duration?: number) {
    this.show(message, "success", duration);
  },
  error(message: string, duration?: number) {
    this.show(message, "error", duration);
  },
  info(message: string, duration?: number) {
    this.show(message, "info", duration);
  },
  warning(message: string, duration?: number) {
    this.show(message, "warning", duration);
  },
};

export function useToastState() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const handler = (t: Toast[]) => setToasts(t);
    toastListeners = [...toastListeners, handler];
    return () => {
      toastListeners = toastListeners.filter((fn) => fn !== handler);
    };
  }, []);

  const dismiss = useCallback((id: string) => {
    toastQueue = toastQueue.filter((t) => t.id !== id);
    notify(toastListeners, toastQueue);
  }, []);

  return { toasts, dismiss };
}

export function useToast() {
  return { toast };
}
