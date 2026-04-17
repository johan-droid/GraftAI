"use client";

import { Box, Typography, Paper, Stack } from "@mui/material";
import { motion } from "framer-motion";
import { ReactNode } from "react";
import Link from "next/link";
import { Calendar, MessageSquare, Sparkles, ShieldCheck } from "lucide-react";

interface AuthLayoutProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
}

const highlights = [
  {
    icon: Calendar,
    title: "Calendar-aware",
    text: "Keep your scheduling context in sync across devices.",
  },
  {
    icon: MessageSquare,
    title: "Copilot ready",
    text: "Move from chat to action without losing the thread.",
  },
  {
    icon: ShieldCheck,
    title: "Private by default",
    text: "Secure sign-in and simple, low-friction access.",
  },
];

export function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  return (
    <Box
      sx={{
        minHeight: "100dvh",
        display: "flex",
        flexDirection: "column",
        alignItems: "stretch",
        justifyContent: { xs: "flex-start", sm: "center" },
        background: "var(--bg-surface)",
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
        <Box sx={{ position: "absolute", top: -120, left: -100, width: 240, height: 240, borderRadius: "50%", bgcolor: "var(--primary-glow)", filter: "blur(80px)" }} />
        <Box sx={{ position: "absolute", bottom: -120, right: -80, width: 240, height: 240, borderRadius: "50%", bgcolor: "rgba(52, 168, 83, 0.08)", filter: "blur(80px)" }} />
      </Box>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        style={{ width: "100%", maxWidth: "1120px", margin: "0 auto", position: "relative", zIndex: 1 }}
      >
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", lg: "0.92fr 1.08fr" },
            gap: { xs: 2, sm: 2.5, lg: 3.5 },
            alignItems: "stretch",
          }}
        >
          <Paper
            elevation={0}
            sx={{
              p: { xs: 3, sm: 4.5 },
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              borderRadius: { xs: "24px", sm: "32px" },
              background: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              boxShadow: "var(--shadow-card)",
            }}
          >
            <Stack spacing={3}>
              <Box sx={{ display: "flex", justifyContent: "flex-start" }}>
                <Box
                  sx={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 1,
                    px: 1.5,
                    py: 0.8,
                    borderRadius: 99,
                    background: "var(--bg-hover)",
                    color: "var(--primary)",
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: "0.18em",
                    textTransform: "uppercase",
                  }}
                >
                  <Sparkles size={12} />
                  GraftAI Workspace
                </Box>
              </Box>

              <Box>
                <Typography
                  component="h2"
                  sx={{
                    fontSize: { xs: "1.5rem", sm: "1.95rem" },
                    lineHeight: 1.08,
                    fontWeight: 600,
                    letterSpacing: "-0.04em",
                    color: "var(--text-primary)",
                    fontFamily: "var(--font-outfit)",
                  }}
                >
                  One account for scheduling, chat, and follow-up.
                </Typography>

                <Typography
                  sx={{
                    mt: 1.5,
                    fontSize: { xs: "0.96rem", sm: "1rem" },
                    lineHeight: 1.6,
                    color: "var(--text-secondary)",
                    fontFamily: "var(--font-sans)",
                    maxWidth: 360,
                  }}
                >
                  Sign in once and keep your calendar, AI copilot, and automation context in
                  one place. Less switching, more momentum.
                </Typography>
              </Box>

              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: { xs: "1fr", sm: "repeat(3, minmax(0, 1fr))", lg: "1fr" },
                  gap: 1.25,
                }}
              >
                {highlights.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Box
                      key={item.title}
                      sx={{
                        display: "flex",
                        gap: 1.5,
                        alignItems: "flex-start",
                        p: 1.5,
                        borderRadius: 4,
                        background: "var(--bg-hover)",
                        border: "1px solid var(--border-subtle)",
                      }}
                    >
                      <Box
                        sx={{
                          width: 36,
                          height: 36,
                          borderRadius: 3,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          background: "var(--primary-glow)",
                          color: "var(--primary)",
                          flexShrink: 0,
                        }}
                      >
                        <Icon size={16} />
                      </Box>
                      <Box>
                        <Typography sx={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)" }}>
                          {item.title}
                        </Typography>
                        <Typography sx={{ mt: 0.4, fontSize: 11.5, lineHeight: 1.5, color: "var(--text-secondary)" }}>
                          {item.text}
                        </Typography>
                      </Box>
                    </Box>
                  );
                })}
              </Box>

              <Box
                sx={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 1,
                }}
              >
                {[
                  "Calendar sync",
                  "Mobile-first",
                  "Private access",
                ].map((tag) => (
                  <Box
                    key={tag}
                    sx={{
                      px: 1.5,
                      py: 0.7,
                      borderRadius: 99,
                      fontSize: 11,
                      fontWeight: 600,
                      color: "var(--text-secondary)",
                      background: "var(--bg-hover)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    {tag}
                  </Box>
                ))}
              </Box>
            </Stack>
          </Paper>

          <Paper
            elevation={0}
            sx={{
              p: { xs: 3, sm: 5 },
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              borderRadius: { xs: "24px", sm: "32px" },
              background: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              boxShadow: "var(--shadow-card)",
            }}
          >
            <Box sx={{ mb: 2, display: "flex", justifyContent: "space-between", width: "100%", alignItems: "center" }}>
              <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: "12px",
                background: "var(--primary)",
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

              <Box
                sx={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 1,
                  px: 1.25,
                  py: 0.75,
                  borderRadius: 99,
                  background: "var(--success-glow)",
                  color: "var(--success)",
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: "0.14em",
                  textTransform: "uppercase",
                }}
              >
                Secure session
              </Box>
            </Box>

            <Typography
              component="h1"
              sx={{
                fontSize: { xs: "1.65rem", sm: "1.85rem" },
                fontWeight: 600,
                color: "var(--text-primary)",
                fontFamily: "var(--font-outfit)",
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
                  color: "var(--text-secondary)",
                  fontFamily: "var(--font-sans)",
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
        </Box>

        <Box sx={{ mt: 3, display: "flex", justifyContent: { xs: "center", sm: "space-between" }, px: 2, flexWrap: "wrap", gap: 2 }}>
          <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap", justifyContent: "center" }}>
            <Link
              href="/terms"
              style={{
                fontSize: "12px",
                color: "var(--text-secondary)",
                textDecoration: "none",
                fontFamily: "var(--font-sans)",
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
