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
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg-base, #f0f4f9)",
        p: 2,
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        style={{ width: "100%", maxWidth: "450px" }}
      >
        <Paper
          elevation={0}
          sx={{
            p: { xs: 4, sm: 5 },
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            borderRadius: "28px",
            background: "var(--bg-elevated, #ffffff)",
            border: "1px solid var(--border-subtle, rgba(0,0,0,0.08))",
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
              fontSize: "1.5rem",
              fontWeight: 400,
              color: "var(--text-primary, #1f1f1f)",
              fontFamily: "var(--font-sans, 'Google Sans', Roboto, sans-serif)",
              mb: 1,
              textAlign: "center",
            }}
          >
            {title}
          </Typography>

          {subtitle && (
            <Typography
              sx={{
                fontSize: "1rem",
                color: "var(--text-secondary, #444746)",
                fontFamily: "var(--font-sans, Roboto, sans-serif)",
                mb: 4,
                textAlign: "center",
              }}
            >
              {subtitle}
            </Typography>
          )}

          <Box sx={{ width: "100%" }}>{children}</Box>
        </Paper>

        <Box sx={{ mt: 3, display: "flex", justifyContent: "space-between", px: 2 }}>
          <Box sx={{ display: "flex", gap: 3 }}>
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
