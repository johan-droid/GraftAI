"use client";

import { useEffect } from "react";
import { signOut } from "next-auth/react";
import { Box, Typography, Stack, CircularProgress } from "@mui/material";
import { motion } from "framer-motion";
import { ShieldAlert, Lock, Zap } from "lucide-react";
import { AuthLayout } from "@/components/auth/AuthLayout";

export default function SignoutPage() {
  useEffect(() => {
    const timer = setTimeout(() => {
      signOut({ callbackUrl: "/goodbye" });
    }, 2800);
    return () => clearTimeout(timer);
  }, []);

  return (
    <AuthLayout
      title="Secure Logout"
      subtitle="GRAFT_AI :: TERMINATING_ACTIVE_SESSION"
    >
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
      >
        <Stack spacing={6} alignItems="center" textAlign="center">
          <Box sx={{ position: "relative" }}>
            <motion.div
              animate={{ 
                rotate: 360,
                scale: [1, 1.1, 1]
              }}
              transition={{ 
                rotate: { duration: 4, repeat: Infinity, ease: "linear" },
                scale: { duration: 2, repeat: Infinity, ease: "easeInOut" }
              }}
            >
              <CircularProgress 
                variant="determinate" 
                value={75} 
                size={80} 
                thickness={2}
                sx={{ color: "var(--primary)", opacity: 0.3 }}
              />
            </motion.div>
            <Box sx={{ 
              position: "absolute", 
              inset: 0, 
              display: "grid", 
              placeItems: "center" 
            }}>
              <Lock size={24} className="text-primary" />
            </Box>
          </Box>

          <Stack spacing={2}>
            <Typography
              sx={{
                fontSize: "12px",
                fontFamily: "var(--font-mono)",
                color: "var(--text-primary)",
                textTransform: "uppercase",
                letterSpacing: "0.2em",
                fontWeight: 800
              }}
            >
              Securing Neural Pathways
            </Typography>
            <Typography
              sx={{
                fontSize: "10px",
                fontFamily: "var(--font-mono)",
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.1em"
              }}
            >
              Syncing local cache components... [OK]
            </Typography>
          </Stack>

          <Box sx={{ 
            width: "100%", 
            height: "2px", 
            bgcolor: "var(--border-subtle)", 
            position: "relative",
            overflow: "hidden"
          }}>
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: "100%" }}
              transition={{ duration: 2.5, repeat: Infinity, ease: "linear" }}
              style={{
                position: "absolute",
                top: 0,
                bottom: 0,
                width: "40%",
                background: "linear-gradient(90deg, transparent, var(--primary), transparent)"
              }}
            />
          </Box>

          <Typography sx={{ fontSize: "9px", color: "var(--text-faint)", fontFamily: "var(--font-mono)" }}>
            [ DO NOT CLOSE THIS WINDOW DURING SESSION TERMINATION ]
          </Typography>
        </Stack>
      </motion.div>
    </AuthLayout>
  );
}
