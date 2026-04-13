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
// Status color mapping
const statusColors = {
  success: {
    bg: "rgba(0, 255, 156, 0.05)",
    border: "var(--primary)",
    text: "var(--primary)",
    icon: CheckCircle,
  },
  warning: {
    bg: "rgba(0, 224, 255, 0.05)",
    border: "var(--secondary)",
    text: "var(--secondary)",
    icon: AlertCircle,
  },
  error: {
    bg: "rgba(255, 0, 122, 0.05)",
    border: "var(--accent)",
    text: "var(--accent)",
    icon: AlertCircle,
  },
  info: {
    bg: "var(--bg-elevated)",
    border: "var(--border-subtle)",
    text: "var(--text-secondary)",
    icon: Activity,
  },
  neutral: {
    bg: "var(--bg-base)",
    border: "var(--border-subtle)",
    text: "var(--text-muted)",
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
      whileHover={onClick ? { y: -2 } : undefined}
      whileTap={onClick ? { scale: 0.99 } : undefined}
      transition={{ duration: 0.2 }}
    >
      <Card
        onClick={onClick}
        className={`relative overflow-hidden ${className || ""}`}
        sx={{
          backgroundColor: "var(--bg-base)",
          border: `1px dashed var(--border-subtle)`,
          borderRadius: "0",
          cursor: onClick ? "pointer" : "default",
          boxShadow: "none",
          transition: "all 0.2s ease",
          "&:hover": {
            borderColor: colors.border,
            background: "var(--bg-elevated)",
          },
        }}
      >
        <CardContent sx={{ padding: styles.padding, "&:last-child": { paddingBottom: styles.padding } }}>
          <Box className="flex items-start justify-between">
            {/* Left content */}
            <Box className="flex-1">
              {/* Title */}
              <Typography
                variant={styles.titleSize as any}
                sx={{
                  color: "var(--text-muted)",
                  fontWeight: 800,
                  textTransform: "uppercase",
                  letterSpacing: "0.15em",
                  mb: 1,
                  fontFamily: "var(--font-mono)",
                  fontSize: "9px",
                }}
              >
                {title}
              </Typography>

              {/* Value */}
              {loading ? (
                <Skeleton variant="text" width="60%" height={40} sx={{ bgcolor: "var(--bg-elevated)" }} />
              ) : (
                <Typography
                  sx={{
                    fontWeight: 900,
                    color: "var(--text-primary)",
                    lineHeight: 1,
                    fontSize: { xs: "1.25rem", md: "1.5rem" },
                    fontFamily: "var(--font-mono)",
                    letterSpacing: "-0.02em",
                  }}
                >
                  {value}
                </Typography>
              )}

              {/* Subtitle */}
              {subtitle && !loading && (
                <Typography
                  sx={{
                    color: "var(--text-muted)",
                    mt: 1,
                    display: "block",
                    fontSize: "11px",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 500
                  }}
                >
                  {subtitle}
                </Typography>
              )}

              {/* Trend */}
              {trend && !loading && (
                <Box className="flex items-center gap-1.5 mt-3">
                  <TrendIcon
                    size={14}
                    style={{ 
                       color: trend.direction === "up" ? "var(--primary)" : "var(--accent)"
                    }}
                  />
                  <Typography
                    sx={{
                      fontSize: "10px",
                      fontWeight: 800,
                      fontFamily: "var(--font-mono)",
                      color: trend.direction === "up" ? "var(--primary)" : "var(--accent)",
                    }}
                  >
                    {trend.value > 0 ? "+" : ""}
                    {trend.value}%
                  </Typography>
                  <Typography sx={{ fontSize: "10px", color: "var(--text-faint)", fontFamily: "var(--font-mono)", fontWeight: 700 }}>
                    {trend.label.toUpperCase()}
                  </Typography>
                </Box>
              )}
            </Box>

            {/* Icon */}
            <Box
              sx={{
                width: styles.iconSize,
                height: styles.iconSize,
                borderRadius: "0",
                backgroundColor: "var(--bg-elevated)",
                border: "1px solid var(--border-subtle)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                ml: 2,
              }}
            >
              <Icon size={styles.iconSize / 2.2} style={{ color: colors.border }} />
            </Box>
          </Box>

          {/* Progress bar */}
          {progress && !loading && (
            <Box className="mt-5">
              <Box className="flex justify-between mb-1.5">
                <Typography sx={{ fontSize: "9px", color: "var(--text-faint)", fontWeight: 800, fontFamily: "var(--font-mono)" }}>
                  {progress.label?.toUpperCase() || "NODE_YIELD"}
                </Typography>
                <Typography sx={{ fontWeight: 800, color: colors.border, fontSize: "9px", fontFamily: "var(--font-mono)" }}>
                  {Math.round((progress.value / progress.max) * 100)}%
                </Typography>
              </Box>
              <Box
                sx={{
                  height: "2px",
                  backgroundColor: "var(--bg-elevated)",
                  borderRadius: "0",
                  overflow: "hidden",
                }}
              >
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(progress.value / progress.max) * 100}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  style={{
                    height: "100%",
                    backgroundColor: colors.border,
                  }}
                />
              </Box>
            </Box>
          )}

          {/* Status chip */}
          {status !== "neutral" && !loading && (
            <Box className="mt-4">
               <div className="inline-flex items-center px-1.5 py-0.5 border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
                  <div className="w-1.5 h-1.5 mr-2 rounded-full animate-pulse" style={{ background: colors.text }} />
                  <span className="text-[9px] font-black uppercase tracking-widest" style={{ color: colors.text }}>
                    {status}
                  </span>
               </div>
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
