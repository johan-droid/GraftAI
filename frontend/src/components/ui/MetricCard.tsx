"use client";

import React from "react";
import { Card, CardContent, Typography, Box, Chip, Skeleton } from "@mui/material";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  Calendar,
  Users,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  type LucideIcon,
} from "lucide-react";

// Types
export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    label: string;
    direction: "up" | "down" | "neutral";
  };
  status?: "success" | "warning" | "error" | "info" | "neutral";
  loading?: boolean;
  onClick?: () => void;
  className?: string;
  size?: "small" | "medium" | "large";
  progress?: {
    value: number;
    max: number;
    label?: string;
  };
}

// Status color mapping
const statusColors = {
  success: {
    bg: "rgba(34, 197, 94, 0.1)",
    border: "rgba(34, 197, 94, 0.2)",
    text: "#22c55e",
    icon: CheckCircle,
  },
  warning: {
    bg: "rgba(234, 179, 8, 0.1)",
    border: "rgba(234, 179, 8, 0.2)",
    text: "#eab308",
    icon: AlertCircle,
  },
  error: {
    bg: "rgba(239, 68, 68, 0.1)",
    border: "rgba(239, 68, 68, 0.2)",
    text: "#ef4444",
    icon: AlertCircle,
  },
  info: {
    bg: "rgba(59, 130, 246, 0.1)",
    border: "rgba(59, 130, 246, 0.2)",
    text: "#3b82f6",
    icon: Activity,
  },
  neutral: {
    bg: "hsl(var(--muted))",
    border: "hsl(var(--border))",
    text: "hsl(var(--muted-foreground))",
    icon: Minus,
  },
};

// Default icons by title keywords
const defaultIcons: Record<string, LucideIcon> = {
  bookings: Calendar,
  users: Users,
  automations: Zap,
  success: CheckCircle,
  failed: AlertCircle,
  pending: Clock,
  time: Clock,
  active: Activity,
};

export function MetricCard({
  title,
  value,
  subtitle,
  icon: CustomIcon,
  trend,
  status = "neutral",
  loading = false,
  onClick,
  className,
  size = "medium",
  progress,
}: MetricCardProps) {
  const colors = statusColors[status];
  const Icon = CustomIcon ||
    Object.entries(defaultIcons).find(([key]) =>
      title.toLowerCase().includes(key)
    )?.[1] ||
    Activity;

  const TrendIcon =
    trend?.direction === "up"
      ? TrendingUp
      : trend?.direction === "down"
      ? TrendingDown
      : Minus;

  const sizeStyles = {
    small: {
      padding: "16px",
      iconSize: 32,
      titleSize: "caption",
      valueSize: "h6",
    },
    medium: {
      padding: "24px",
      iconSize: 40,
      titleSize: "body2",
      valueSize: "h5",
    },
    large: {
      padding: "32px",
      iconSize: 48,
      titleSize: "body1",
      valueSize: "h4",
    },
  };

  const styles = sizeStyles[size];

  return (
    <motion.div
      whileHover={onClick ? { scale: 1.02, y: -2 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      transition={{ type: "spring", stiffness: 400, damping: 17 }}
    >
      <Card
        onClick={onClick}
        className={`relative overflow-hidden ${className || ""}`}
        sx={{
          backgroundColor: "hsl(var(--card))",
          border: `1px solid ${colors.border}`,
          borderRadius: "16px",
          cursor: onClick ? "pointer" : "default",
          boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          transition: "box-shadow 0.2s ease, border-color 0.2s ease",
          "&:hover": onClick
            ? {
                boxShadow: "0 8px 25px rgba(0,0,0,0.1)",
                borderColor: colors.text,
              }
            : undefined,
        }}
      >
        {/* Background gradient accent */}
        <Box
          sx={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: "3px",
            background: `linear-gradient(90deg, ${colors.text} 0%, ${colors.bg} 100%)`,
          }}
        />

        <CardContent sx={{ padding: styles.padding, "&:last-child": { paddingBottom: styles.padding } }}>
          <Box className="flex items-start justify-between">
            {/* Left content */}
            <Box className="flex-1">
              {/* Title */}
              <Typography
                variant={styles.titleSize as any}
                sx={{
                  color: "hsl(var(--muted-foreground))",
                  fontWeight: 500,
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  mb: 0.5,
                }}
              >
                {title}
              </Typography>

              {/* Value */}
              {loading ? (
                <Skeleton variant="text" width="60%" height={40} />
              ) : (
                <Typography
                  variant={styles.valueSize as any}
                  sx={{
                    fontWeight: 700,
                    color: "hsl(var(--foreground))",
                    lineHeight: 1.2,
                  }}
                >
                  {value}
                </Typography>
              )}

              {/* Subtitle */}
              {subtitle && !loading && (
                <Typography
                  variant="caption"
                  sx={{
                    color: "hsl(var(--muted-foreground))",
                    mt: 0.5,
                    display: "block",
                  }}
                >
                  {subtitle}
                </Typography>
              )}

              {/* Trend */}
              {trend && !loading && (
                <Box className="flex items-center gap-1 mt-2">
                  <TrendIcon
                    size={16}
                    color={
                      trend.direction === "up"
                        ? "#22c55e"
                        : trend.direction === "down"
                        ? "#ef4444"
                        : "#6b7280"
                    }
                  />
                  <Typography
                    variant="caption"
                    sx={{
                      fontWeight: 600,
                      color:
                        trend.direction === "up"
                          ? "#22c55e"
                          : trend.direction === "down"
                          ? "#ef4444"
                          : "#6b7280",
                    }}
                  >
                    {trend.value > 0 ? "+" : ""}
                    {trend.value}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {trend.label}
                  </Typography>
                </Box>
              )}
            </Box>

            {/* Icon */}
            <Box
              sx={{
                width: styles.iconSize,
                height: styles.iconSize,
                borderRadius: "12px",
                backgroundColor: colors.bg,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                ml: 2,
              }}
            >
              <Icon size={styles.iconSize / 2} color={colors.text} />
            </Box>
          </Box>

          {/* Progress bar */}
          {progress && !loading && (
            <Box className="mt-4">
              <Box className="flex justify-between mb-1">
                <Typography variant="caption" color="text.secondary">
                  {progress.label || "Progress"}
                </Typography>
                <Typography variant="caption" sx={{ fontWeight: 600, color: colors.text }}>
                  {Math.round((progress.value / progress.max) * 100)}%
                </Typography>
              </Box>
              <Box
                sx={{
                  height: "6px",
                  backgroundColor: "hsl(var(--muted))",
                  borderRadius: "3px",
                  overflow: "hidden",
                }}
              >
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(progress.value / progress.max) * 100}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  style={{
                    height: "100%",
                    backgroundColor: colors.text,
                    borderRadius: "3px",
                  }}
                />
              </Box>
            </Box>
          )}

          {/* Status chip */}
          {status !== "neutral" && !loading && (
            <Box className="mt-3">
              <Chip
                size="small"
                label={status.replace(/_/g, " ").toUpperCase()}
                sx={{
                  backgroundColor: colors.bg,
                  color: colors.text,
                  fontWeight: 600,
                  fontSize: "0.7rem",
                  borderRadius: "4px",
                }}
              />
            </Box>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Metric Card Grid Component
export interface MetricCardGridProps {
  children: React.ReactNode;
  columns?: 1 | 2 | 3 | 4 | 5 | 6;
  gap?: number;
  className?: string;
}

export function MetricCardGrid({
  children,
  columns = 4,
  gap = 3,
  className,
}: MetricCardGridProps) {
  const gridTemplateColumns = {
    1: "1fr",
    2: "repeat(2, 1fr)",
    3: "repeat(3, 1fr)",
    4: "repeat(4, 1fr)",
    5: "repeat(5, 1fr)",
    6: "repeat(6, 1fr)",
  };

  return (
    <Box
      className={className}
      sx={{
        display: "grid",
        gridTemplateColumns: {
          xs: "1fr",
          sm: columns >= 2 ? "repeat(2, 1fr)" : "1fr",
          md: gridTemplateColumns[columns],
        },
        gap: gap * 8, // MUI spacing unit
      }}
    >
      {children}
    </Box>
  );
}

export default MetricCard;
