"use client";

import React from "react";
import { Box, Typography, Button, Paper } from "@mui/material";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  RefreshCw,
  WifiOff,
  ServerCrash,
  Lock,
  HelpCircle,
  ArrowLeft,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";

// Types
export interface ErrorStateProps {
  title?: string;
  description?: string;
  error?: Error | string | null;
  errorCode?: string;
  onRetry?: () => void;
  onBack?: () => void;
  backHref?: string;
  backLabel?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: "primary" | "secondary";
  };
  variant?: "error" | "warning" | "info" | "offline" | "unauthorized" | "not-found";
  icon?: LucideIcon;
  size?: "small" | "medium" | "large";
  showDetails?: boolean;
  fullHeight?: boolean;
  className?: string;
}

// Error variant configurations
const errorConfigs: Record<string, { icon: LucideIcon; color: string; bgColor: string; defaultTitle: string; defaultDesc: string }> = {
  error: {
    icon: AlertTriangle,
    color: "#ef4444",
    bgColor: "rgba(239, 68, 68, 0.1)",
    defaultTitle: "Something went wrong",
    defaultDesc: "We encountered an unexpected error. Please try again.",
  },
  warning: {
    icon: AlertTriangle,
    color: "#eab308",
    bgColor: "rgba(234, 179, 8, 0.1)",
    defaultTitle: "Warning",
    defaultDesc: "There might be an issue. Please check your connection.",
  },
  info: {
    icon: HelpCircle,
    color: "#3b82f6",
    bgColor: "rgba(59, 130, 246, 0.1)",
    defaultTitle: "Information",
    defaultDesc: "Here's what you need to know.",
  },
  offline: {
    icon: WifiOff,
    color: "#6b7280",
    bgColor: "rgba(107, 114, 128, 0.1)",
    defaultTitle: "You're offline",
    defaultDesc: "Please check your internet connection and try again.",
  },
  unauthorized: {
    icon: Lock,
    color: "#dc2626",
    bgColor: "rgba(220, 38, 38, 0.1)",
    defaultTitle: "Access denied",
    defaultDesc: "You don't have permission to access this resource. Please sign in.",
  },
  "not-found": {
    icon: HelpCircle,
    color: "#6b7280",
    bgColor: "rgba(107, 114, 128, 0.1)",
    defaultTitle: "Page not found",
    defaultDesc: "The page you're looking for doesn't exist or has been moved.",
  },
};

export function ErrorState({
  title,
  description,
  error,
  errorCode,
  onRetry,
  onBack,
  backHref,
  backLabel = "Go back",
  action,
  variant = "error",
  icon: CustomIcon,
  size = "medium",
  showDetails = false,
  fullHeight = false,
  className,
}: ErrorStateProps) {
  const config = errorConfigs[variant];
  const Icon = CustomIcon || config.icon;
  
  const displayTitle = title || config.defaultTitle;
  const displayDesc = description || config.defaultDesc;
  
  // Format error details
  const errorDetails = React.useMemo(() => {
    if (!showDetails || !error) return null;
    if (typeof error === "string") return error;
    return error.message || String(error);
  }, [error, showDetails]);

  const sizeStyles = {
    small: {
      iconSize: 48,
      padding: "24px",
      titleSize: "h6",
      descSize: "body2",
    },
    medium: {
      iconSize: 64,
      padding: "32px",
      titleSize: "h5",
      descSize: "body1",
    },
    large: {
      iconSize: 80,
      padding: "48px",
      titleSize: "h4",
      descSize: "body1",
    },
  };

  const s = sizeStyles[size];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={className}
    >
      <Paper
        elevation={0}
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: fullHeight ? "center" : "flex-start",
          minHeight: fullHeight ? "60vh" : "auto",
          padding: s.padding,
          textAlign: "center",
          backgroundColor: "transparent",
        }}
      >
        {/* Icon */}
        <Box
          sx={{
            width: s.iconSize,
            height: s.iconSize,
            borderRadius: "50%",
            backgroundColor: config.bgColor,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            mb: 2,
          }}
        >
          <Icon size={s.iconSize / 2} color={config.color} />
        </Box>

        {/* Error code */}
        {errorCode && (
          <Typography
            variant="caption"
            sx={{
              color: config.color,
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              mb: 1,
            }}
          >
            Error {errorCode}
          </Typography>
        )}

        {/* Title */}
        <Typography
          variant={s.titleSize as any}
          sx={{
            fontWeight: 700,
            color: "hsl(var(--foreground))",
            mb: 1,
          }}
        >
          {displayTitle}
        </Typography>

        {/* Description */}
        <Typography
          variant={s.descSize as any}
          sx={{
            color: "hsl(var(--muted-foreground))",
            maxWidth: 400,
            mb: 3,
          }}
        >
          {displayDesc}
        </Typography>

        {/* Error details */}
        {errorDetails && (
          <Paper
            sx={{
              p: 2,
              mb: 3,
              backgroundColor: "hsl(var(--muted))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              maxWidth: 500,
              width: "100%",
            }}
          >
            <Typography
              variant="caption"
              sx={{
                fontFamily: "monospace",
                color: "hsl(var(--muted-foreground))",
                wordBreak: "break-word",
              }}
            >
              {errorDetails}
            </Typography>
          </Paper>
        )}

        {/* Actions */}
        <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", justifyContent: "center" }}>
          {/* Retry button */}
          {onRetry && (
            <Button
              variant="contained"
              onClick={onRetry}
              startIcon={<RefreshCw size={18} />}
              sx={{
                backgroundColor: config.color,
                "&:hover": { backgroundColor: config.color, opacity: 0.9 },
                textTransform: "none",
              }}
            >
              Try again
            </Button>
          )}

          {/* Custom action */}
          {action && (
            <Button
              variant={action.variant === "primary" ? "contained" : "outlined"}
              onClick={action.onClick}
              sx={{
                textTransform: "none",
                ...(action.variant === "primary" && {
                  backgroundColor: config.color,
                  "&:hover": { backgroundColor: config.color, opacity: 0.9 },
                }),
              }}
            >
              {action.label}
            </Button>
          )}

          {/* Back button */}
          {(onBack || backHref) && (
            backHref ? (
              <Link href={backHref} style={{ textDecoration: "none" }}>
                <Button
                  variant="outlined"
                  startIcon={<ArrowLeft size={18} />}
                  sx={{
                    borderColor: "hsl(var(--border))",
                    color: "hsl(var(--foreground))",
                    textTransform: "none",
                  }}
                >
                  {backLabel}
                </Button>
              </Link>
            ) : (
              <Button
                variant="outlined"
                onClick={onBack}
                startIcon={<ArrowLeft size={18} />}
                sx={{
                  borderColor: "hsl(var(--border))",
                  color: "hsl(var(--foreground))",
                  textTransform: "none",
                }}
              >
                {backLabel}
              </Button>
            )
          )}
        </Box>
      </Paper>
    </motion.div>
  );
}

// Specialized error states
export function OfflineState(props: Omit<ErrorStateProps, "variant">) {
  return <ErrorState {...props} variant="offline" />;
}

export function UnauthorizedState(props: Omit<ErrorStateProps, "variant">) {
  return <ErrorState {...props} variant="unauthorized" />;
}

export function NotFoundState(props: Omit<ErrorStateProps, "variant">) {
  return <ErrorState {...props} variant="not-found" />;
}

export function ServerErrorState(props: Omit<ErrorStateProps, "variant">) {
  return <ErrorState {...props} variant="error" icon={ServerCrash} />;
}

export default ErrorState;
