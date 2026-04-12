"use client";

import { Box } from "@mui/material";
import { ReactNode } from "react";

type BadgeVariant = "default" | "primary" | "success" | "warning" | "error" | "info";
type BadgeSize = "sm" | "md" | "lg";

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  pulse?: boolean;
}

const variants: Record<BadgeVariant, { bg: string; color: string; border: string }> = {
  default: {
    bg: "hsl(240, 24%, 18%)",
    color: "hsl(215, 16%, 70%)",
    border: "hsla(239, 84%, 67%, 0.1)",
  },
  primary: {
    bg: "hsla(239, 84%, 67%, 0.15)",
    color: "hsl(239, 84%, 67%)",
    border: "hsla(239, 84%, 67%, 0.3)",
  },
  success: {
    bg: "hsla(160, 84%, 39%, 0.15)",
    color: "hsl(160, 84%, 39%)",
    border: "hsla(160, 84%, 39%, 0.3)",
  },
  warning: {
    bg: "hsla(38, 92%, 50%, 0.15)",
    color: "hsl(38, 92%, 50%)",
    border: "hsla(38, 92%, 50%, 0.3)",
  },
  error: {
    bg: "hsla(346, 84%, 61%, 0.15)",
    color: "hsl(346, 84%, 61%)",
    border: "hsla(346, 84%, 61%, 0.3)",
  },
  info: {
    bg: "hsla(199, 89%, 48%, 0.15)",
    color: "hsl(199, 89%, 48%)",
    border: "hsla(199, 89%, 48%, 0.3)",
  },
};

const sizes: Record<BadgeSize, { px: number; py: number; fontSize: string }> = {
  sm: { px: 1.5, py: 0.25, fontSize: "0.625rem" },
  md: { px: 2, py: 0.5, fontSize: "0.75rem" },
  lg: { px: 2.5, py: 0.75, fontSize: "0.875rem" },
};

export function Badge({
  children,
  variant = "default",
  size = "md",
  dot = false,
  pulse = false,
}: BadgeProps) {
  const { bg, color, border } = variants[variant];
  const { px, py, fontSize } = sizes[size];

  return (
    <Box
      sx={{
        display: "inline-flex",
        alignItems: "center",
        gap: 1,
        px,
        py,
        background: bg,
        border: `1px solid ${border}`,
        borderRadius: 10,
        color,
        fontSize,
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        whiteSpace: "nowrap",
      }}
    >
      {dot && (
        <Box
          sx={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: color,
            ...(pulse && {
              animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
              "@keyframes pulse": {
                "0%, 100%": { opacity: 1 },
                "50%": { opacity: 0.5 },
              },
            }),
          }}
        />
      )}
      {children}
    </Box>
  );
}

// Status badges with predefined icons
export function StatusBadge({
  status,
  size = "md",
}: {
  status: "online" | "offline" | "away" | "busy" | "new" | "beta" | "pro";
  size?: BadgeSize;
}) {
  const configs = {
    online: { variant: "success" as const, label: "Online", dot: true, pulse: true },
    offline: { variant: "default" as const, label: "Offline", dot: true, pulse: false },
    away: { variant: "warning" as const, label: "Away", dot: true, pulse: false },
    busy: { variant: "error" as const, label: "Busy", dot: true, pulse: false },
    new: { variant: "primary" as const, label: "New", dot: false, pulse: false },
    beta: { variant: "info" as const, label: "Beta", dot: false, pulse: false },
    pro: { variant: "warning" as const, label: "Pro", dot: false, pulse: false },
  };

  const config = configs[status];
  return (
    <Badge
      variant={config.variant}
      size={size}
      dot={config.dot}
      pulse={config.pulse}
    >
      {config.label}
    </Badge>
  );
}

// Number badge for notifications
export function NotificationBadge({
  count,
  max = 99,
}: {
  count: number;
  max?: number;
}) {
  if (count <= 0) return null;

  const display = count > max ? `${max}+` : count;

  return (
    <Box
      sx={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        minWidth: 20,
        height: 20,
        px: 0.75,
        background: "hsl(346, 84%, 61%)",
        borderRadius: 10,
        color: "white",
        fontSize: "0.6875rem",
        fontWeight: 700,
      }}
    >
      {display}
    </Box>
  );
}

// Count badge (small, inline)
export function CountBadge({ count }: { count: number }) {
  return (
    <Box
      component="span"
      sx={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        px: 1,
        py: 0.25,
        background: "hsl(240, 24%, 18%)",
        borderRadius: 1,
        color: "hsl(215, 16%, 70%)",
        fontSize: "0.75rem",
        fontWeight: 600,
        ml: 1,
      }}
    >
      {count}
    </Box>
  );
}
