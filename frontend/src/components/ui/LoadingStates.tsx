"use client";

import React from "react";
import { Box, Typography, Paper, Skeleton, LinearProgress, Chip } from "@mui/material";
import { motion } from "framer-motion";
import {
  Loader2,
  Brain,
  Eye,
  Zap,
  CheckCircle,
  Sparkles,
} from "lucide-react";

// ═══════════════════════════════════════════════════════════════════
// PULSE LOADER
// ═══════════════════════════════════════════════════════════════════

export interface PulseLoaderProps {
  size?: number;
  color?: string;
  gap?: number;
}

export function PulseLoader({ size = 8, color = "hsl(239, 84%, 67%)", gap = 4 }: PulseLoaderProps) {
  return (
    <Box sx={{ display: "flex", gap: `${gap}px`, alignItems: "center" }}>
      {[0, 1, 2].map((i) => (
        <Box
          key={i}
          component={motion.div}
          animate={{
            scale: [0.6, 1, 0.6],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 1.4,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 0.2,
          }}
          sx={{
            width: size,
            height: size,
            borderRadius: "50%",
            backgroundColor: color,
          }}
        />
      ))}
    </Box>
  );
}

// ═══════════════════════════════════════════════════════════════════
// AI THINKING INDICATOR
// ═══════════════════════════════════════════════════════════════════

export interface AIThinkingProps {
  phase?: "perception" | "cognition" | "action" | "reflection" | "idle";
  message?: string;
  size?: "small" | "medium" | "large";
}

const phaseConfig = {
  perception: { icon: Eye, label: "Perceiving", color: "#3b82f6" },
  cognition: { icon: Brain, label: "Thinking", color: "#8b5cf6" },
  action: { icon: Zap, label: "Executing", color: "#f59e0b" },
  reflection: { icon: CheckCircle, label: "Reflecting", color: "#22c55e" },
  idle: { icon: Sparkles, label: "Processing", color: "hsl(239, 84%, 67%)" },
};

export function AIThinking({ phase = "idle", message, size = "medium" }: AIThinkingProps) {
  const config = phaseConfig[phase];
  const Icon = config.icon;
  
  const sizeStyles = {
    small: { iconSize: 16, fontSize: "0.75rem", padding: "8px 12px" },
    medium: { iconSize: 20, fontSize: "0.875rem", padding: "12px 16px" },
    large: { iconSize: 24, fontSize: "1rem", padding: "16px 20px" },
  };
  
  const s = sizeStyles[size];
  
  return (
    <Box
      sx={{
        display: "inline-flex",
        alignItems: "center",
        gap: 1.5,
        padding: s.padding,
        borderRadius: "12px",
        backgroundColor: `${config.color}10`,
        border: `1px solid ${config.color}20`,
      }}
    >
      <Box
        component={motion.div}
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
      >
        <Icon size={s.iconSize} color={config.color} />
      </Box>
      <Typography
        sx={{
          fontSize: s.fontSize,
          fontWeight: 500,
          color: config.color,
        }}
      >
        {message || config.label}...
      </Typography>
    </Box>
  );
}

// ═══════════════════════════════════════════════════════════════════
// PAGE LOADING SKELETON
// ═══════════════════════════════════════════════════════════════════

export interface PageSkeletonProps {
  variant?: "dashboard" | "list" | "detail" | "form" | "chat";
}

export function PageSkeleton({ variant = "dashboard" }: PageSkeletonProps) {
  const renderDashboard = () => (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 3 }}>
        <Box>
          <Skeleton variant="text" width={200} height={32} />
          <Skeleton variant="text" width={150} height={20} sx={{ mt: 1 }} />
        </Box>
        <Skeleton variant="circular" width={40} height={40} />
      </Box>
      
      {/* Stat cards */}
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)", md: "repeat(4, 1fr)" }, gap: 2, mb: 3 }}>
        {[1, 2, 3, 4].map((i) => (
          <Paper key={i} sx={{ p: 2, borderRadius: "16px" }}>
            <Skeleton variant="text" width="60%" height={16} />
            <Skeleton variant="text" width="40%" height={32} sx={{ mt: 1 }} />
            <Skeleton variant="text" width="30%" height={14} sx={{ mt: 1 }} />
          </Paper>
        ))}
      </Box>
      
      {/* Content area */}
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "2fr 1fr" }, gap: 2 }}>
        <Paper sx={{ p: 3, borderRadius: "16px" }}>
          <Skeleton variant="text" width="40%" height={24} />
          {[1, 2, 3, 4, 5].map((i) => (
            <Box key={i} sx={{ display: "flex", gap: 2, mt: 2 }}>
              <Skeleton variant="circular" width={40} height={40} />
              <Box sx={{ flex: 1 }}>
                <Skeleton variant="text" width="80%" />
                <Skeleton variant="text" width="60%" />
              </Box>
            </Box>
          ))}
        </Paper>
        <Paper sx={{ p: 3, borderRadius: "16px" }}>
          <Skeleton variant="text" width="50%" height={24} />
          {[1, 2, 3].map((i) => (
            <Box key={i} sx={{ display: "flex", gap: 2, mt: 2 }}>
              <Skeleton variant="rounded" width={36} height={36} sx={{ borderRadius: "8px" }} />
              <Box sx={{ flex: 1 }}>
                <Skeleton variant="text" width="70%" />
                <Skeleton variant="text" width="40%" />
              </Box>
            </Box>
          ))}
        </Paper>
      </Box>
    </Box>
  );

  const renderList = () => (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 3 }}>
        <Skeleton variant="text" width={180} height={28} />
        <Skeleton variant="rounded" width={120} height={36} sx={{ borderRadius: "8px" }} />
      </Box>
      {/* Search bar */}
      <Skeleton variant="rounded" width="100%" height={44} sx={{ borderRadius: "12px", mb: 2 }} />
      {/* Table rows */}
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <Box key={i} sx={{ display: "flex", gap: 2, py: 1.5, borderBottom: "1px solid hsl(var(--border))" }}>
          <Skeleton variant="text" width="25%" />
          <Skeleton variant="text" width="20%" />
          <Skeleton variant="rounded" width={60} height={24} sx={{ borderRadius: "4px" }} />
          <Skeleton variant="text" width="15%" />
        </Box>
      ))}
    </Box>
  );

  const renderDetail = () => (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
        <Skeleton variant="rounded" width={36} height={36} sx={{ borderRadius: "8px" }} />
        <Skeleton variant="text" width={200} height={28} />
      </Box>
      <Paper sx={{ p: 3, borderRadius: "16px", mb: 2 }}>
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Box key={i} sx={{ display: "flex", gap: 2, mb: 2 }}>
            <Skeleton variant="text" width="30%" />
            <Skeleton variant="text" width="60%" />
          </Box>
        ))}
      </Paper>
    </Box>
  );

  const renderForm = () => (
    <Box sx={{ p: 3, maxWidth: 600 }}>
      <Skeleton variant="text" width={180} height={28} sx={{ mb: 3 }} />
      {[1, 2, 3, 4, 5].map((i) => (
        <Box key={i} sx={{ mb: 2.5 }}>
          <Skeleton variant="text" width="40%" height={16} sx={{ mb: 1 }} />
          <Skeleton variant="rounded" width="100%" height={44} sx={{ borderRadius: "8px" }} />
        </Box>
      ))}
      <Box sx={{ display: "flex", gap: 2, mt: 3 }}>
        <Skeleton variant="rounded" width={120} height={40} sx={{ borderRadius: "8px" }} />
        <Skeleton variant="rounded" width={100} height={40} sx={{ borderRadius: "8px" }} />
      </Box>
    </Box>
  );

  const renderChat = () => (
    <Box sx={{ p: 3, display: "flex", flexDirection: "column", height: "100%" }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 3 }}>
        <Skeleton variant="text" width={150} height={28} />
      </Box>
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
        {[1, 2, 3].map((i) => (
          <Box key={i} sx={{ display: "flex", gap: 2, flexDirection: i % 2 === 0 ? "row-reverse" : "row" }}>
            <Skeleton variant="circular" width={36} height={36} />
            <Skeleton variant="rounded" width="60%" height={60} sx={{ borderRadius: "12px" }} />
          </Box>
        ))}
      </Box>
      <Box sx={{ display: "flex", gap: 1, mt: 2 }}>
        <Skeleton variant="rounded" width="100%" height={48} sx={{ borderRadius: "12px" }} />
        <Skeleton variant="circular" width={44} height={44} />
      </Box>
    </Box>
  );

  switch (variant) {
    case "dashboard": return renderDashboard();
    case "list": return renderList();
    case "detail": return renderDetail();
    case "form": return renderForm();
    case "chat": return renderChat();
    default: return renderDashboard();
  }
}

// ═══════════════════════════════════════════════════════════════════
// SPINNER OVERLAY
// ═══════════════════════════════════════════════════════════════════

export interface SpinnerOverlayProps {
  message?: string;
  transparent?: boolean;
}

export function SpinnerOverlay({ message, transparent = false }: SpinnerOverlayProps) {
  return (
    <Box
      sx={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: transparent ? "transparent" : "rgba(0, 0, 0, 0.3)",
        backdropFilter: transparent ? "none" : "blur(4px)",
        zIndex: 1000,
        gap: 2,
      }}
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        style={{
          width: 40,
          height: 40,
          borderRadius: "50%",
          border: "3px solid hsla(239, 84%, 67%, 0.2)",
          borderTopColor: "hsl(239, 84%, 67%)",
        }}
      />
      {message && (
        <Typography
          sx={{
            color: "hsl(var(--foreground))",
            fontWeight: 500,
            fontSize: "0.875rem",
          }}
        >
          {message}
        </Typography>
      )}
    </Box>
  );
}

// ═══════════════════════════════════════════════════════════════════
// PROGRESS STEPPER
// ═══════════════════════════════════════════════════════════════════

export interface ProgressStep {
  label: string;
  status: "pending" | "in_progress" | "completed" | "error";
}

export interface ProgressStepperProps {
  steps: ProgressStep[];
  orientation?: "horizontal" | "vertical";
  size?: "small" | "medium";
}

export function ProgressStepper({ steps, orientation = "horizontal", size = "medium" }: ProgressStepperProps) {
  const statusIcons: Record<string, React.ReactNode> = {
    pending: <Box sx={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: "hsl(var(--muted-foreground))" }} />,
    in_progress: <Loader2 size={size === "small" ? 14 : 18} className="animate-spin" color="hsl(239, 84%, 67%)" />,
    completed: <CheckCircle size={size === "small" ? 14 : 18} color="#22c55e" />,
    error: <Box sx={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: "#ef4444" }} />,
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: orientation === "horizontal" ? "row" : "column",
        gap: orientation === "horizontal" ? 3 : 2,
        alignItems: orientation === "horizontal" ? "center" : "flex-start",
      }}
    >
      {steps.map((step, index) => (
        <Box
          key={index}
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}
        >
          {statusIcons[step.status]}
          <Typography
            variant={size === "small" ? "caption" : "body2"}
            sx={{
              fontWeight: step.status === "in_progress" ? 600 : 400,
              color: step.status === "pending" ? "hsl(var(--muted-foreground))" : "hsl(var(--foreground))",
            }}
          >
            {step.label}
          </Typography>
        </Box>
      ))}
    </Box>
  );
}

export default PageSkeleton;
