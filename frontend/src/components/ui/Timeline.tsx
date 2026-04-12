"use client";

import React from "react";
import { Box, Typography, Chip, Tooltip, LinearProgress } from "@mui/material";
import { motion } from "framer-motion";
import {
  Eye,
  Brain,
  Zap,
  CheckCircle,
  Clock,
  AlertCircle,
  Loader2,
  type LucideIcon,
} from "lucide-react";

// Types
export interface TimelinePhase {
  id: string;
  title: string;
  description: string;
  status: "pending" | "in_progress" | "completed" | "failed" | "skipped";
  duration_ms?: number;
  timestamp?: string;
  icon?: LucideIcon;
  details?: {
    label: string;
    value: string | number;
  }[];
  error?: string;
  logs?: string[];
}

export interface TimelineProps {
  phases: TimelinePhase[];
  title?: string;
  subtitle?: string;
  showProgress?: boolean;
  orientation?: "vertical" | "horizontal";
  size?: "small" | "medium" | "large";
  className?: string;
  onPhaseClick?: (phase: TimelinePhase) => void;
  expandedPhaseId?: string | null;
  currentPhaseId?: string;
}

// Phase icon mapping
const defaultIcons: Record<string, LucideIcon> = {
  perception: Eye,
  cognition: Brain,
  action: Zap,
  reflection: CheckCircle,
  reasoning: Brain,
  default: Clock,
};

// Status color and style mapping
const statusStyles = {
  pending: {
    bg: "hsl(var(--muted))",
    border: "hsl(var(--border))",
    color: "hsl(var(--muted-foreground))",
    iconColor: "#9ca3af",
    progress: 0,
  },
  in_progress: {
    bg: "rgba(59, 130, 246, 0.1)",
    border: "#3b82f6",
    color: "#3b82f6",
    iconColor: "#3b82f6",
    progress: 50,
  },
  completed: {
    bg: "rgba(34, 197, 94, 0.1)",
    border: "#22c55e",
    color: "#22c55e",
    iconColor: "#22c55e",
    progress: 100,
  },
  failed: {
    bg: "rgba(239, 68, 68, 0.1)",
    border: "#ef4444",
    color: "#ef4444",
    iconColor: "#ef4444",
    progress: 100,
  },
  skipped: {
    bg: "hsl(var(--muted))",
    border: "hsl(var(--border))",
    color: "hsl(var(--muted-foreground))",
    iconColor: "#9ca3af",
    progress: 100,
  },
};

// Format duration helper
const formatDuration = (ms?: number): string => {
  if (!ms) return "—";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
};

// Single Timeline Phase Component
function TimelinePhaseCard({
  phase,
  index,
  total,
  size,
  onClick,
  isExpanded,
  isCurrent,
  orientation,
}: {
  phase: TimelinePhase;
  index: number;
  total: number;
  size: "small" | "medium" | "large";
  onClick?: () => void;
  isExpanded: boolean;
  isCurrent: boolean;
  orientation: "vertical" | "horizontal";
}) {
  const styles = statusStyles[phase.status];
  const Icon =
    phase.icon ||
    defaultIcons[phase.id.toLowerCase()] ||
    defaultIcons.default;

  const isLast = index === total - 1;

  const sizeStyles = {
    small: {
      nodeSize: 32,
      iconSize: 16,
      titleSize: "body2",
      descSize: "caption",
      padding: "12px",
    },
    medium: {
      nodeSize: 40,
      iconSize: 20,
      titleSize: "body1",
      descSize: "body2",
      padding: "16px",
    },
    large: {
      nodeSize: 48,
      iconSize: 24,
      titleSize: "h6",
      descSize: "body1",
      padding: "20px",
    },
  };

  const s = sizeStyles[size];

  return (
    <Box
      className={`relative flex ${orientation === "vertical" ? "flex-row" : "flex-col"} items-start`}
      sx={{ flex: orientation === "horizontal" ? 1 : undefined }}
    >
      {/* Connection line */}
      {!isLast && (
        <Box
          sx={{
            position: "absolute",
            ...(orientation === "vertical"
              ? {
                  left: s.nodeSize / 2 - 1,
                  top: s.nodeSize,
                  width: "2px",
                  height: "calc(100% - 8px)",
                }
              : {
                  top: s.nodeSize / 2 - 1,
                  left: s.nodeSize,
                  height: "2px",
                  width: "calc(100% - 8px)",
                }),
            backgroundColor:
              phase.status === "completed" || phase.status === "failed"
                ? styles.border
                : "hsl(var(--border))",
          }}
        />
      )}

      {/* Phase node */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: index * 0.1 }}
        whileHover={onClick ? { scale: 1.1 } : undefined}
        onClick={onClick}
        style={{
          width: s.nodeSize,
          height: s.nodeSize,
          borderRadius: "50%",
          backgroundColor: styles.bg,
          border: `2px solid ${styles.border}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: onClick ? "pointer" : "default",
          zIndex: 1,
          flexShrink: 0,
        }}
      >
        {phase.status === "in_progress" ? (
          <Loader2 size={s.iconSize} color={styles.iconColor} className="animate-spin" />
        ) : (
          <Icon size={s.iconSize} color={styles.iconColor} />
        )}

        {/* Current phase pulse effect */}
        {isCurrent && phase.status === "in_progress" && (
          <Box
            component={motion.div}
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.5, 0, 0.5],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            sx={{
              position: "absolute",
              width: s.nodeSize + 8,
              height: s.nodeSize + 8,
              borderRadius: "50%",
              border: `2px solid ${styles.border}`,
            }}
          />
        )}
      </motion.div>

      {/* Phase content */}
      <Box
        sx={{
          marginLeft: orientation === "vertical" ? 2 : 0,
          marginTop: orientation === "vertical" ? 0 : 1.5,
          flex: 1,
          width: orientation === "horizontal" ? "100%" : undefined,
          minWidth: 0, // Prevent flex item overflow
        }}
      >
        {/* Header */}
        <Box className="flex items-start justify-between gap-2">
          <Box className="flex-1 min-w-0">
            <Typography
              variant={s.titleSize as any}
              sx={{
                fontWeight: 600,
                color: "hsl(var(--foreground))",
                display: "flex",
                alignItems: "center",
                gap: 1,
              }}
            >
              {phase.title}
              {phase.status === "failed" && (
                <Tooltip title={phase.error || "Failed"}>
                  <AlertCircle size={16} color="#ef4444" />
                </Tooltip>
              )}
            </Typography>
            <Typography
              variant={s.descSize as any}
              sx={{
                color: "hsl(var(--muted-foreground))",
                mt: 0.5,
              }}
            >
              {phase.description}
            </Typography>
          </Box>

          {/* Duration badge */}
          {phase.duration_ms !== undefined && (
            <Chip
              size="small"
              label={formatDuration(phase.duration_ms)}
              sx={{
                backgroundColor: styles.bg,
                color: styles.color,
                fontWeight: 500,
                fontSize: "0.75rem",
                height: "24px",
                flexShrink: 0,
              }}
            />
          )}
        </Box>

        {/* Status indicator */}
        <Box className="mt-2">
          <Chip
            size="small"
            label={phase.status.replace("_", " ").toUpperCase()}
            sx={{
              backgroundColor: styles.bg,
              color: styles.color,
              fontWeight: 600,
              fontSize: "0.7rem",
              borderRadius: "4px",
              height: "20px",
            }}
          />
        </Box>

        {/* Progress bar for in_progress */}
        {phase.status === "in_progress" && (
          <LinearProgress
            sx={{
              mt: 1.5,
              height: 4,
              borderRadius: 2,
              backgroundColor: "hsl(var(--muted))",
              "& .MuiLinearProgress-bar": {
                backgroundColor: styles.color,
                borderRadius: 2,
              },
            }}
          />
        )}

        {/* Expanded details */}
        {isExpanded && phase.details && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mt-3"
          >
            <Box
              sx={{
                backgroundColor: "hsl(var(--muted))",
                borderRadius: "8px",
                padding: "12px",
              }}
            >
              <Typography variant="caption" sx={{ fontWeight: 600, mb: 1, display: "block" }}>
                Details
              </Typography>
              {phase.details.map((detail, i) => (
                <Box key={i} className="flex justify-between py-1">
                  <Typography variant="caption" color="text.secondary">
                    {detail.label}
                  </Typography>
                  <Typography variant="caption" sx={{ fontWeight: 500 }}>
                    {detail.value}
                  </Typography>
                </Box>
              ))}

              {/* Logs */}
              {phase.logs && phase.logs.length > 0 && (
                <Box className="mt-2">
                  <Typography variant="caption" sx={{ fontWeight: 600, mb: 0.5, display: "block" }}>
                    Logs
                  </Typography>
                  <Box
                    component="pre"
                    sx={{
                      fontSize: "0.7rem",
                      fontFamily: "monospace",
                      backgroundColor: "rgba(0,0,0,0.05)",
                      padding: "8px",
                      borderRadius: "4px",
                      maxHeight: "100px",
                      overflow: "auto",
                      m: 0,
                    }}
                  >
                    {phase.logs.join("\n")}
                  </Box>
                </Box>
              )}
            </Box>
          </motion.div>
        )}

        {/* Error message */}
        {phase.error && phase.status === "failed" && (
          <Box
            sx={{
              mt: 1.5,
              p: 1.5,
              backgroundColor: "rgba(239, 68, 68, 0.05)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
              borderRadius: "6px",
            }}
          >
            <Typography variant="caption" color="error" sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <AlertCircle size={12} />
              {phase.error}
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
}

// Main Timeline Component
export function Timeline({
  phases,
  title,
  subtitle,
  showProgress = true,
  orientation = "vertical",
  size = "medium",
  className,
  onPhaseClick,
  expandedPhaseId,
  currentPhaseId,
}: TimelineProps) {
  const completedPhases = phases.filter((p) => p.status === "completed").length;
  const progress = phases.length > 0 ? (completedPhases / phases.length) * 100 : 0;

  return (
    <Box className={className}>
      {/* Header */}
      {(title || subtitle || showProgress) && (
        <Box className="mb-4">
          {title && (
            <Typography variant="h6" sx={{ fontWeight: 600, mb: subtitle ? 0.5 : 0 }}>
              {title}
            </Typography>
          )}
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
          {showProgress && (
            <Box className="mt-3">
              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: "hsl(var(--muted))",
                  "& .MuiLinearProgress-bar": {
                    backgroundColor: "#22c55e",
                    borderRadius: 3,
                  },
                }}
              />
              <Typography variant="caption" color="text.secondary" className="mt-1 block">
                {completedPhases} of {phases.length} phases completed ({Math.round(progress)}%)
              </Typography>
            </Box>
          )}
        </Box>
      )}

      {/* Timeline phases */}
      <Box
        sx={{
          display: "flex",
          flexDirection: orientation === "vertical" ? "column" : "row",
          gap: orientation === "vertical" ? 3 : 2,
        }}
      >
        {phases.map((phase, index) => (
          <TimelinePhaseCard
            key={phase.id}
            phase={phase}
            index={index}
            total={phases.length}
            size={size}
            onClick={onPhaseClick ? () => onPhaseClick(phase) : undefined}
            isExpanded={expandedPhaseId === phase.id}
            isCurrent={currentPhaseId === phase.id}
            orientation={orientation}
          />
        ))}
      </Box>
    </Box>
  );
}

// Agent Execution Timeline - Specialized for 4-phase loop
export interface AgentExecutionTimelineProps {
  perception?: {
    status: TimelinePhase["status"];
    duration_ms?: number;
    details?: TimelinePhase["details"];
    logs?: string[];
    error?: string;
  };
  cognition?: {
    status: TimelinePhase["status"];
    duration_ms?: number;
    decision?: string;
    confidence?: string;
    details?: TimelinePhase["details"];
    logs?: string[];
    error?: string;
  };
  action?: {
    status: TimelinePhase["status"];
    duration_ms?: number;
    actions_executed?: number;
    total_actions?: number;
    details?: TimelinePhase["details"];
    logs?: string[];
    error?: string;
  };
  reflection?: {
    status: TimelinePhase["status"];
    duration_ms?: number;
    assessment?: string;
    details?: TimelinePhase["details"];
    logs?: string[];
    error?: string;
  };
  size?: "small" | "medium" | "large";
  className?: string;
}

export function AgentExecutionTimeline({
  perception,
  cognition,
  action,
  reflection,
  size = "medium",
  className,
}: AgentExecutionTimelineProps) {
  const phases: TimelinePhase[] = [
    {
      id: "perception",
      title: "Perception",
      description: "Gather context from booking data, attendee profile, and previous interactions",
      status: perception?.status || "pending",
      duration_ms: perception?.duration_ms,
      icon: Eye,
      details: perception?.details,
      logs: perception?.logs,
      error: perception?.error,
    },
    {
      id: "cognition",
      title: "Cognition",
      description: "Analyze risk, assess attendee priority, and decide optimal actions",
      status: cognition?.status || "pending",
      duration_ms: cognition?.duration_ms,
      icon: Brain,
      details: cognition?.decision
        ? [
            ...(cognition.details || []),
            { label: "Decision", value: cognition.decision },
            { label: "Confidence", value: cognition.confidence || "—" },
          ]
        : cognition?.details,
      logs: cognition?.logs,
      error: cognition?.error,
    },
    {
      id: "action",
      title: "Action",
      description: "Execute tools: send emails, create calendar events, update CRM",
      status: action?.status || "pending",
      duration_ms: action?.duration_ms,
      icon: Zap,
      details: action?.actions_executed !== undefined
        ? [
            ...(action.details || []),
            { label: "Actions Executed", value: `${action.actions_executed}/${action.total_actions || action.actions_executed}` },
          ]
        : action?.details,
      logs: action?.logs,
      error: action?.error,
    },
    {
      id: "reflection",
      title: "Reflection",
      description: "Assess outcomes, update memory, and store learnings",
      status: reflection?.status || "pending",
      duration_ms: reflection?.duration_ms,
      icon: CheckCircle,
      details: reflection?.assessment
        ? [
            ...(reflection.details || []),
            { label: "Assessment", value: reflection.assessment },
          ]
        : reflection?.details,
      logs: reflection?.logs,
      error: reflection?.error,
    },
  ];

  return (
    <Timeline
      phases={phases}
      title="Agent Execution"
      subtitle="4-Phase AI Agent Loop"
      size={size}
      className={className}
    />
  );
}

export default Timeline;
