"use client";

import { CheckCircle2, Clock3, RotateCcw, XCircle, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type BookingStatusKey = "confirmed" | "pending" | "cancelled" | "rescheduled" | "unknown";

interface BookingStatusPillProps {
  status: string;
  isDark?: boolean;
  className?: string;
}

const statusConfig: Record<BookingStatusKey, { label: string; Icon: LucideIcon; light: string; dark: string }> = {
  confirmed: {
    label: "Confirmed",
    Icon: CheckCircle2,
    light: "border-emerald-200 bg-emerald-50 text-emerald-700",
    dark: "border-emerald-500/20 bg-emerald-500/10 text-emerald-200",
  },
  pending: {
    label: "Pending",
    Icon: Clock3,
    light: "border-amber-200 bg-amber-50 text-amber-700",
    dark: "border-amber-500/20 bg-amber-500/10 text-amber-200",
  },
  cancelled: {
    label: "Cancelled",
    Icon: XCircle,
    light: "border-rose-200 bg-rose-50 text-rose-700",
    dark: "border-rose-500/20 bg-rose-500/10 text-rose-200",
  },
  rescheduled: {
    label: "Rescheduled",
    Icon: RotateCcw,
    light: "border-violet-200 bg-violet-50 text-violet-700",
    dark: "border-violet-500/20 bg-violet-500/10 text-violet-200",
  },
  unknown: {
    label: "Status",
    Icon: Clock3,
    light: "border-slate-200 bg-slate-50 text-slate-600",
    dark: "border-slate-500/20 bg-slate-500/10 text-slate-300",
  },
};

function normalizeStatus(status: string): BookingStatusKey {
  const resolved = status.trim().toLowerCase();

  if (resolved === "confirmed" || resolved === "pending" || resolved === "rescheduled") {
    return resolved;
  }

  if (resolved === "cancelled" || resolved === "canceled") {
    return "cancelled";
  }

  return "unknown";
}

export default function BookingStatusPill({ status, isDark = false, className }: BookingStatusPillProps) {
  const statusKey = normalizeStatus(status);
  const config = statusConfig[statusKey];
  const StatusIcon = config.Icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.22em] whitespace-nowrap",
        isDark ? config.dark : config.light,
        className
      )}
    >
      <StatusIcon className="h-3.5 w-3.5 shrink-0" />
      {config.label}
    </span>
  );
}