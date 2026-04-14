"use client";

import { Box, Typography, Skeleton } from "@mui/material";
import { motion } from "framer-motion";
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { getThemeColors } from "@/lib/theme";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    label: string;
  };
  color?: "primary" | "success" | "warning" | "info" | "error";
  isLoading?: boolean;
  delay?: number;
}

export function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  color = "primary",
  isLoading,
  delay = 0,
}: StatCardProps) {
  const { isDark } = useTheme();

  const colorMap = {
    primary: { bg: "var(--bg-hover)", border: "var(--primary)", icon: "var(--primary)" },
    success: { bg: "var(--bg-hover)", border: "var(--primary)", icon: "var(--primary)" },
    warning: { bg: "var(--bg-hover)", border: "var(--secondary)", icon: "var(--secondary)" },
    info: { bg: "var(--bg-hover)", border: "var(--secondary)", icon: "var(--secondary)" },
    error: { bg: "var(--bg-hover)", border: "var(--accent)", icon: "var(--accent)" },
  };

  const theme = colorMap[color];
  const isPositive = trend && trend.value >= 0;

  if (isLoading) {
    return (
      <Box
        sx={{
          p: { xs: 2, md: 3 },
          background: "var(--bg-base)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "0",
        }}
      >
        <Skeleton width={40} height={40} sx={{ bgcolor: "var(--bg-elevated)", mb: 2 }} />
        <Skeleton width="60%" height={28} sx={{ bgcolor: "var(--bg-elevated)", mb: 1 }} />
        <Skeleton width="40%" height={20} sx={{ bgcolor: "var(--bg-elevated)" }} />
      </Box>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.3 }}
    >
      <Box
        sx={{
          p: { xs: 2, md: 2.5 },
          background: "var(--bg-base)",
          border: `1px solid var(--border-subtle)`,
          borderRadius: "0",
          position: "relative",
          overflow: "hidden",
          transition: "all 0.2s ease",
          "&:hover": {
            borderColor: theme.border,
            background: "var(--bg-elevated)",
            boxShadow: `0 0 20px -10px ${theme.border}`,
          },
        }}
      >
        <Box sx={{ position: "relative", zIndex: 1 }}>
          {/* Header */}
          <Box sx={{ display: "flex", alignItems: "flex-start", justifyBaseline: "space-between", mb: 3 }}>
            <Box
              sx={{
                width: 40,
                height: 40,
                border: `1px solid var(--border-subtle)`,
                background: "var(--bg-elevated)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "0",
              }}
            >
              <Icon size={18} style={{ color: theme.icon }} />
            </Box>

            <Box sx={{ ml: "auto" }}>
              {trend && (
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 0.5,
                    px: 1,
                    py: 0.5,
                    background: isPositive 
                      ? "rgba(0, 255, 156, 0.05)" 
                      : "rgba(255, 0, 122, 0.05)",
                    border: `1px solid ${isPositive ? "rgba(0, 255, 156, 0.2)" : "rgba(255, 0, 122, 0.2)"}`,
                  }}
                >
                  <Typography
                    sx={{
                      fontSize: "10px",
                      fontWeight: 800,
                      color: isPositive ? "var(--primary)" : "var(--accent)",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {isPositive ? "▲" : "▼"} {Math.abs(trend.value)}%
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>

          {/* Title */}
          <Typography
            sx={{
              fontSize: "10px",
              color: "var(--text-muted)",
              fontWeight: 800,
              fontFamily: "var(--font-mono)",
              textTransform: "uppercase",
              letterSpacing: "0.15em",
              mb: 1,
            }}
          >
            {title}
          </Typography>

          {/* Value */}
          <Typography
            sx={{
              fontSize: { xs: "1.5rem", md: "1.85rem" },
              fontWeight: 900,
              color: "var(--text-primary)",
              fontFamily: "var(--font-mono)",
              lineHeight: 1,
              letterSpacing: "-0.05em",
            }}
          >
            {value}
          </Typography>

          {/* Detail Line */}
          <Box sx={{ mt: 2, pt: 1, borderTop: "1px solid var(--border-subtle)", opacity: 0.5 }}>
            <Typography sx={{ fontSize: "9px", color: "var(--text-faint)", fontFamily: "var(--font-mono)", textTransform: "uppercase" }}>
              {trend?.label || "SYSTEM_ACTIVE"}
            </Typography>
          </Box>
        </Box>
      </Box>
    </motion.div>
  );
}
