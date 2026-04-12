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
  const colors = getThemeColors(isDark ? "dark" : "light");

  const colorMap = {
    primary: { bg: "hsla(239, 84%, 67%, 0.15)", border: "hsla(239, 84%, 67%, 0.3)", icon: "hsl(239, 84%, 67%)" },
    success: { bg: "hsla(160, 84%, 39%, 0.15)", border: "hsla(160, 84%, 39%, 0.3)", icon: "hsl(160, 84%, 39%)" },
    warning: { bg: "hsla(38, 92%, 50%, 0.15)", border: "hsla(38, 92%, 50%, 0.3)", icon: "hsl(38, 92%, 50%)" },
    info: { bg: "hsla(199, 89%, 48%, 0.15)", border: "hsla(199, 89%, 48%, 0.3)", icon: "hsl(199, 89%, 48%)" },
    error: { bg: "hsla(346, 84%, 61%, 0.15)", border: "hsla(346, 84%, 61%, 0.3)", icon: "hsl(346, 84%, 61%)" },
  };

  const theme = colorMap[color];
  const isPositive = trend && trend.value >= 0;

  if (isLoading) {
    return (
      <Box
        sx={{
          p: { xs: 2, md: 3 },
          background: isDark 
            ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
            : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
          border: "1px solid hsla(239, 84%, 67%, 0.1)",
          borderRadius: "16px",
        }}
      >
        <Skeleton width={40} height={40} sx={{ bgcolor: "hsla(239, 84%, 67%, 0.1)", mb: 2 }} />
        <Skeleton width="60%" height={28} sx={{ bgcolor: "hsla(239, 84%, 67%, 0.1)", mb: 1 }} />
        <Skeleton width="40%" height={20} sx={{ bgcolor: "hsla(239, 84%, 67%, 0.1)" }} />
      </Box>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: "easeOut" }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
    >
      <Box
        sx={{
          p: { xs: 2, md: 3 },
          background: isDark 
            ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
            : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
          border: `1px solid ${theme.border}`,
          borderRadius: "16px",
          position: "relative",
          overflow: "hidden",
          transition: "all 0.3s ease",
          boxShadow: isDark ? "0 4px 20px rgba(0, 0, 0, 0.3)" : "0 4px 20px rgba(0, 0, 0, 0.05)",
          "&:hover": {
            boxShadow: isDark 
              ? "0 8px 30px rgba(0, 0, 0, 0.4)" 
              : "0 8px 30px rgba(0, 0, 0, 0.1)",
            borderColor: theme.border.replace("0.3", "0.5"),
          },
        }}
      >
        {/* Background Glow */}
        <Box
          sx={{
            position: "absolute",
            top: -50,
            right: -50,
            width: 150,
            height: 150,
            background: `radial-gradient(circle, ${theme.bg} 0%, transparent 70%)`,
            opacity: 0.5,
            pointerEvents: "none",
          }}
        />

        <Box sx={{ position: "relative", zIndex: 1 }}>
          {/* Header */}
          <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", mb: 2 }}>
            <Box
              sx={{
                width: 44,
                height: 44,
                borderRadius: "12px",
                background: theme.bg,
                border: `1px solid ${theme.border}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Icon size={22} style={{ color: theme.icon }} />
            </Box>

            {trend && (
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.5,
                  px: 1.5,
                  py: 0.5,
                  borderRadius: "20px",
                  background: isPositive 
                    ? "hsla(160, 84%, 39%, 0.15)" 
                    : "hsla(346, 84%, 61%, 0.15)",
                  border: isPositive 
                    ? "1px solid hsla(160, 84%, 39%, 0.3)" 
                    : "1px solid hsla(346, 84%, 61%, 0.3)",
                }}
              >
                {isPositive ? (
                  <TrendingUp size={14} style={{ color: "hsl(160, 84%, 39%)" }} />
                ) : (
                  <TrendingDown size={14} style={{ color: "hsl(346, 84%, 61%)" }} />
                )}
                <Typography
                  sx={{
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: isPositive ? "hsl(160, 84%, 39%)" : "hsl(346, 84%, 61%)",
                  }}
                >
                  {isPositive ? "+" : ""}{trend.value}%
                </Typography>
              </Box>
            )}
          </Box>

          {/* Value */}
          <Typography
            variant="h4"
            sx={{
              fontSize: { xs: "1.5rem", md: "1.75rem" },
              fontWeight: 700,
              color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
              mb: 0.5,
              letterSpacing: "-0.02em",
            }}
          >
            {value}
          </Typography>

          {/* Title */}
          <Typography
            sx={{
              fontSize: "0.875rem",
              color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
              fontWeight: 500,
            }}
          >
            {title}
          </Typography>

          {/* Trend Label */}
          {trend && (
            <Typography
              sx={{
                fontSize: "0.75rem",
                color: isDark ? "hsl(215, 16%, 40%)" : "hsl(215, 16%, 60%)",
                mt: 1,
              }}
            >
              {trend.label}
            </Typography>
          )}
        </Box>
      </Box>
    </motion.div>
  );
}
