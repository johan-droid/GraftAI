"use client";

import { Box, Typography, Skeleton } from "@mui/material";
import { motion } from "framer-motion";
import { getGreeting, formatUserName } from "@/lib/theme";
import { Sparkles } from "lucide-react";

interface GreetingProps {
  userName?: string;
  userEmail?: string;
  isLoading?: boolean;
}

export function Greeting({ userName, userEmail, isLoading }: GreetingProps) {
  // Minimal display name and simple greeting
  const displayName = userName || (userEmail ? formatUserName(userEmail) : "Guest");
  const simpleName = displayName.split(" ")[0];
  const { emoji } = getGreeting(displayName);
  
  // Get current date
  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  if (isLoading) {
    return (
      <Box sx={{ mb: 4 }}>
        <Skeleton width={300} height={40} sx={{ bgcolor: "hsla(239, 84%, 67%, 0.1)" }} />
        <Skeleton width={200} height={20} sx={{ bgcolor: "hsla(239, 84%, 67%, 0.1)", mt: 1 }} />
      </Box>
    );
  }

  return (
    <Box sx={{ mb: { xs: 4, md: 6 } }}>
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
          <div className="flex items-center gap-2 mb-1">
            <div className="px-2 py-0.5 bg-[var(--primary)] text-black text-[9px] font-semibold rounded-sm">
              Live
            </div>
            <div className="text-[12px] text-[var(--text-faint)] font-medium font-mono">{displayName}</div>
          </div>
          <Typography
            sx={{
              fontSize: { xs: "1.25rem", sm: "1.5rem", md: "1.75rem" },
              fontWeight: 700,
              color: "var(--text-primary)",
              lineHeight: 1.1,
            }}
          >
            {`Welcome back${simpleName ? `, ${simpleName}` : ""}`} <span className="ml-2">{emoji}</span>
          </Typography>
        </Box>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.5 }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 2, mt: 1.5 }}>
          <Typography
            sx={{
              color: "var(--text-muted)",
              fontSize: "11px",
              display: "flex",
              alignItems: "center",
              gap: 1,
              fontFamily: "var(--font-mono)",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.1em"
            }}
          >
            [ {today} ]
          </Typography>
          
          <div className="h-[1px] flex-1 bg-dashed border-b border-dashed border-[var(--border-subtle)] opacity-50" />
          
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              color: "var(--primary)",
              fontSize: "10px",
              fontWeight: 800,
              fontFamily: "var(--font-mono)",
              textTransform: "uppercase",
              letterSpacing: "0.05em"
            }}
          >
            <Sparkles size={14} className="animate-pulse" />
            <span>CORTEX_RELIANCE: OPTIMAL</span>
          </Box>
        </Box>
      </motion.div>
    </Box>
  );
}
