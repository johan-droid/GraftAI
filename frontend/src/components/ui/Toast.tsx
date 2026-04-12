"use client";
/**
 * Enhanced toast system with precise HSL color grading
 * Import { toast } from "@/components/ui/Toast" everywhere.
 */
import { toast as sonner, Toaster as SonnerToaster } from "sonner";
import { CheckCircle2, XCircle, AlertTriangle, Info, Loader2 } from "lucide-react";
import { ReactNode } from "react";

// HSL Color definitions from design system
const colors = {
  success: "hsl(160, 84%, 39%)",
  successBg: "hsla(160, 84%, 39%, 0.1)",
  successBorder: "hsla(160, 84%, 39%, 0.3)",
  
  error: "hsl(346, 84%, 61%)",
  errorBg: "hsla(346, 84%, 61%, 0.1)",
  errorBorder: "hsla(346, 84%, 61%, 0.3)",
  
  warning: "hsl(38, 92%, 50%)",
  warningBg: "hsla(38, 92%, 50%, 0.1)",
  warningBorder: "hsla(38, 92%, 50%, 0.3)",
  
  info: "hsl(199, 89%, 48%)",
  infoBg: "hsla(199, 89%, 48%, 0.1)",
  infoBorder: "hsla(199, 89%, 48%, 0.3)",
  
  bgCard: "hsl(240, 24%, 14%)",
  textPrimary: "hsl(220, 20%, 98%)",
  textSecondary: "hsl(215, 16%, 70%)",
};

export function Toaster() {
  return (
    <SonnerToaster
      position="bottom-right"
      toastOptions={{
        duration: 4000,
        style: {
          background: colors.bgCard,
          border: "1px solid hsla(239, 84%, 67%, 0.2)",
          color: colors.textPrimary,
          borderRadius: "12px",
          fontSize: "14px",
          boxShadow: "0 10px 30px -10px rgba(0,0,0,0.5)",
        },
      }}
    />
  );
}

export const toast = {
  success: (msg: string) =>
    sonner.success(msg, {
      icon: null,
    }),
  error: (msg: string) =>
    sonner.error(msg, {
      icon: null,
    }),
  warning: (msg: string) =>
    sonner.warning(msg, {
      icon: null,
    }),
  info: (msg: string) =>
    sonner.info(msg, {
      icon: null,
    }),
  loading: (msg: string) =>
    sonner.loading(msg, {
      icon: <Loader2 size={18} style={{ color: colors.info, animation: "spin 1s linear infinite" }} />,
    }),
  promise: sonner.promise,
  dismiss: sonner.dismiss,
  custom: (content: ReactNode, options?: { duration?: number }) =>
    sonner.custom(() => content as React.ReactElement, { duration: options?.duration ?? 4000 }),
};
