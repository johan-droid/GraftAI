"use client";
/**
 * Centralized toast helpers wrapping sonner.
 * Import { toast } from "@/components/ui/Toast" everywhere.
 */
import { toast as sonner, Toaster as SonnerToaster } from "sonner";
import { CheckCircle2, XCircle, AlertTriangle, Info } from "lucide-react";

export function Toaster() {
  return (
    <SonnerToaster
      position="bottom-right"
      toastOptions={{
        duration: 4000,
        style: {
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          color: "var(--text)",
          borderRadius: "var(--radius-lg)",
          fontSize: "14px",
          boxShadow: "var(--shadow-card)",
        },
      }}
    />
  );
}

export const toast = {
  success: (msg: string) =>
    sonner.success(msg, {
      icon: <CheckCircle2 className="w-4 h-4" style={{ color: "var(--success)" }} />,
    }),
  error: (msg: string) =>
    sonner.error(msg, {
      icon: <XCircle className="w-4 h-4" style={{ color: "var(--error)" }} />,
    }),
  warning: (msg: string) =>
    sonner.warning(msg, {
      icon: <AlertTriangle className="w-4 h-4" style={{ color: "var(--warning)" }} />,
    }),
  info: (msg: string) =>
    sonner.info(msg, {
      icon: <Info className="w-4 h-4" style={{ color: "var(--info)" }} />,
    }),
  loading: (msg: string) => sonner.loading(msg),
  promise: sonner.promise,
  dismiss: sonner.dismiss,
};
