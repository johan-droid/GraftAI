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
  // Get display name from username, email, or fallback
  const displayName = userName || (userEmail ? formatUserName(userEmail) : "Guest");
  
  // Get time-based greeting
  const { text, emoji } = getGreeting(displayName);
  
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
    <Box sx={{ mb: { xs: 3, md: 4 } }}>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
          <Typography
            variant="h4"
            sx={{
              fontSize: { xs: "1.5rem", sm: "1.75rem", md: "2rem" },
              fontWeight: 700,
              background: "linear-gradient(135deg, hsl(220, 20%, 98%) 0%, hsl(215, 16%, 70%) 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              letterSpacing: "-0.02em",
              display: "flex",
              alignItems: "center",
              gap: 0.5,
            }}
          >
            {text}
            <motion.span
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
              style={{ display: "inline-block" }}
            >
              {emoji}
            </motion.span>
          </Typography>
        </Box>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.4 }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
          <Typography
            variant="body2"
            sx={{
              color: "hsl(215, 16%, 55%)",
              fontSize: "0.9375rem",
              display: "flex",
              alignItems: "center",
              gap: 1,
            }}
          >
            {today}
          </Typography>
          
          <Box
            sx={{
              width: 4,
              height: 4,
              borderRadius: "50%",
              background: "hsl(215, 16%, 40%)",
              mx: 0.5,
            }}
          />
          
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 0.5,
              color: "hsl(239, 84%, 67%)",
              fontSize: "0.8125rem",
              fontWeight: 500,
            }}
          >
            <Sparkles size={14} />
            <span>AI Powered</span>
          </Box>
        </Box>
      </motion.div>
    </Box>
  );
}
