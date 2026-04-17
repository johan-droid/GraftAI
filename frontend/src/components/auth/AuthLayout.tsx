"use client";

import { Box, Typography, Paper } from "@mui/material";
import { motion } from "framer-motion";
import { ReactNode } from "react";
import Link from "next/link";

interface AuthLayoutProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
}

export function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  return (
    <Box
      sx={{
        minHeight: "100dvh",
        display: "flex",
        flexDirection: "column",
        alignItems: "stretch",
        justifyContent: { xs: "flex-start", sm: "center" },
        background:
          "radial-gradient(circle at top left, rgba(26, 115, 232, 0.12), transparent 32%), radial-gradient(circle at bottom right, rgba(52, 168, 83, 0.10), transparent 28%), var(--bg-base, #f0f4f9)",
        p: { xs: 1.5, sm: 2.5 },
        position: "relative",
        overflow: "hidden",
      }}
    >
      <Box
        aria-hidden
        sx={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          opacity: 0.8,
        }}
      >
        <Box sx={{ position: "absolute", top: -120, left: -100, width: 240, height: 240, borderRadius: "50%", bgcolor: "rgba(26, 115, 232, 0.08)", filter: "blur(80px)" }} />
        <Box sx={{ position: "absolute", bottom: -120, right: -80, width: 240, height: 240, borderRadius: "50%", bgcolor: "rgba(52, 168, 83, 0.08)", filter: "blur(80px)" }} />
      </Box>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        style={{ width: "100%", maxWidth: "460px", margin: "0 auto", position: "relative", zIndex: 1 }}
      >
        <Paper
          elevation={0}
          sx={{
            p: { xs: 3, sm: 5 },
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            borderRadius: { xs: "24px", sm: "32px" },
            background: "rgba(255, 255, 255, 0.88)",
            border: "1px solid var(--border-subtle, rgba(0,0,0,0.08))",
            boxShadow: "0 24px 80px -32px rgba(32, 33, 36, 0.28)",
            backdropFilter: "blur(24px)",
          }}
        >
          <Box sx={{ mb: 2, display: "flex", justifyContent: "center" }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: "12px",
                background: "var(--primary, #1a73e8)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontWeight: "bold",
                fontSize: "24px",
              }}
            >
              G
            </Box>
          </Box>

          <Typography
            component="h1"
            sx={{
              fontSize: { xs: "1.65rem", sm: "1.85rem" },
              fontWeight: 500,
              color: "var(--text-primary, #1f1f1f)",
              fontFamily: "var(--font-outfit, var(--font-sans, 'Google Sans', Roboto, sans-serif))",
              mb: 1,
              textAlign: "center",
              letterSpacing: "-0.03em",
            }}
          >
            {title}
          </Typography>

          {subtitle && (
            <Typography
              sx={{
                fontSize: { xs: "0.95rem", sm: "1rem" },
                color: "var(--text-secondary, #444746)",
                fontFamily: "var(--font-sans, Roboto, sans-serif)",
                mb: 4,
                textAlign: "center",
                maxWidth: 320,
              }}
            >
              {subtitle}
            </Typography>
          )}

          <Box sx={{ width: "100%" }}>{children}</Box>
        </Paper>

        <Box sx={{ mt: 3, display: "flex", justifyContent: { xs: "center", sm: "space-between" }, px: 2, flexWrap: "wrap", gap: 2 }}>
          <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap", justifyContent: "center" }}>
            <Link
              href="/terms"
              style={{
                fontSize: "12px",
                color: "var(--text-secondary, #444746)",
                textDecoration: "none",
                fontFamily: "var(--font-sans, Roboto, sans-serif)",
                fontWeight: 500,
              }}
            >
              Terms
            </Link>
            <Link
              href="/privacy"
              style={{
                fontSize: "12px",
                color: "var(--text-secondary, #444746)",
                textDecoration: "none",
                fontFamily: "var(--font-sans, Roboto, sans-serif)",
                fontWeight: 500,
              }}
            >
              Privacy
            </Link>
          </Box>
        </Box>
      </motion.div>
    </Box>
  );
}
