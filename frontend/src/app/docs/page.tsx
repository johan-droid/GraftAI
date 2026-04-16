"use client";

import { Box, Container, Typography, Stack, Grid, Button, alpha } from "@mui/material";
import { motion } from "framer-motion";
import Link from "next/link";
import { 
  ArrowLeft, 
  BookOpenText, 
  CalendarClock, 
  Code2, 
  ShieldCheck, 
  Workflow,
  Terminal,
  ChevronRight
} from "lucide-react";
import { Navigation } from "@/components/landing/Navigation";
import { Footer } from "@/components/landing/Footer";
import DotField from "@/components/landing/DotField";
import "@/components/landing/DotField.css";

const sections = [
  {
    icon: <Workflow className="text-primary" />,
    title: "Kernel Architecture",
    code: "KERN_ARCH_v1",
    body: "GraftAI runs as a high-performance monolith: FastAPI backend, Next.js frontend, async SQLAlchemy models, and worker-driven async jobs for non-blocking workflows.",
    bullets: [
      "FastAPI + SQLAlchemy async models",
      "Public booking routes with signed action tokens",
      "Worker cron for calendar and booking reminders",
    ],
  },
  {
    icon: <CalendarClock className="text-primary" />,
    title: "Orchestration Flow",
    code: "ORCH_LOGIC_v3",
    body: "Public booking supports availability calculation, conflict prevention, confirmations, reschedule, and cancellation with email lifecycle updates.",
    bullets: [
      "Timezone-aware slot generation",
      "Tokenized attendee management links",
      "Calendar event synchronization updates",
    ],
  },
  {
    icon: <ShieldCheck className="text-primary" />,
    title: "Security Protocols",
    code: "SEC_BASE_v2",
    body: "Security headers, trusted host checks, auth token validation, and per-route rate limiting protect critical API workflows.",
    bullets: [
      "HSTS and strict frame policies",
      "HMAC action token verification",
      "Rate limits for booking endpoints",
    ],
  },
  {
    icon: <Code2 className="text-primary" />,
    title: "Embed Modules",
    code: "EMBED_LOADER_v1",
    body: "Embed booking directly into external websites through the GraftAI embed loader and dedicated iframe route.",
    bullets: [
      "Drop-in script: /graftai-embed.js",
      "Autoload via data-graftai-embed",
      "Direct username-based route support",
    ],
  },
];

export default function DocsPage() {
  return (
    <Box sx={{ bgcolor: "var(--bg-base)", minHeight: "100vh", position: "relative" }}>
      <Box sx={{ position: "fixed", inset: 0, zIndex: 0, opacity: 0.4, pointerEvents: "none" }}>
        <DotField />
      </Box>

      <Navigation />

      <Container maxWidth="lg" sx={{ pt: { xs: 20, md: 24 }, pb: 20, position: "relative", zIndex: 1 }}>
        <Stack spacing={2} sx={{ mb: 12 }}>
          <Button
            component={Link}
            href="/"
            startIcon={<ArrowLeft size={16} />}
            sx={{ 
              alignSelf: "start", 
              color: "var(--text-faint)", 
              fontSize: 12, 
              fontFamily: "var(--font-mono)",
              "&:hover": { color: "var(--primary)" }
            }}
          >
            RETURN_TO_CORE
          </Button>

          <Stack direction={{ xs: "column", md: "row" }} spacing={4} alignItems="flex-start" justifyContent="space-between">
            <Box>
              <Typography
                variant="h1"
                className="text-gradient-neon"
                sx={{
                  fontWeight: 900,
                  fontSize: { xs: 42, md: 64 },
                  letterSpacing: "-0.04em",
                  lineHeight: 1,
                  mb: 2
                }}
              >
                Kernel Docs
              </Typography>
              <Typography sx={{ color: "var(--text-muted)", fontSize: 16, maxWidth: 600 }}>
                System-level documentation for the GraftAI orchestration track. Architecture, operational safety, and rollout conventions.
              </Typography>
            </Box>
            
            <Box className="refined-glass" sx={{ p: 2, borderRadius: 2, display: "flex", gap: 2, alignItems: "center" }}>
              <Box className="system-status-dot" />
              <Typography sx={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--primary)", fontWeight: 800 }}>
                DOCS_LIVE_v3.0.82
              </Typography>
            </Box>
          </Stack>
        </Stack>

        <Grid container spacing={3} sx={{ mb: 12 }}>
          {sections.map((section, idx) => (
            <Grid item xs={12} md={6} key={section.title}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                style={{ height: "100%" }}
              >
                <Box className="refined-glass" sx={{ 
                  p: 4, 
                  height: "100%", 
                  borderRadius: 2,
                  display: "flex",
                  flexDirection: "column",
                  "&:hover": { borderColor: "var(--primary)", transition: "0.3s" }
                }}>
                  <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
                    <Box sx={{ p: 1, bgcolor: "rgba(0, 255, 156, 0.05)", borderRadius: 1 }}>
                      {section.icon}
                    </Box>
                    <Typography sx={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-faint)" }}>
                      // {section.code}
                    </Typography>
                  </Stack>

                  <Typography variant="h5" sx={{ fontWeight: 800, mb: 2, color: "var(--text-primary)" }}>
                    {section.title}
                  </Typography>
                  <Typography sx={{ color: "var(--text-muted)", fontSize: 13, mb: 4, lineHeight: 1.6 }}>
                    {section.body}
                  </Typography>

                  <Stack spacing={1.5} sx={{ mt: "auto" }}>
                    {section.bullets.map((bullet) => (
                      <Stack key={bullet} direction="row" spacing={1.5} alignItems="center">
                        <ChevronRight size={12} className="text-primary opacity-50" />
                        <Typography sx={{ fontSize: 12, color: "var(--text-secondary)", fontWeight: 500 }}>{bullet}</Typography>
                      </Stack>
                    ))}
                  </Stack>
                </Box>
              </motion.div>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ 
          p: 6, 
          borderRadius: 2, 
          bgcolor: "rgba(255,255,255,0.01)", 
          border: "1px dashed var(--border-subtle)",
          position: "relative",
          overflow: "hidden"
        }}>
          <Box sx={{ position: "relative", zIndex: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 900, mb: 4, display: "flex", alignItems: "center", gap: 2 }}>
              <Terminal size={24} className="text-primary" /> System Implementation
            </Typography>
            
            <Grid container spacing={6}>
              <Grid item xs={12} md={6}>
                <Typography sx={{ color: "var(--text-muted)", fontSize: 14, mb: 4, lineHeight: 1.6 }}>
                  For production readiness, ensure neural reminders remain enabled in workers, monitor synchronization delivery logs, and verify public action token flows after any kernel refactor.
                </Typography>
                <Stack direction="row" spacing={2}>
                  <Button
                    component={Link}
                    href="/pricing"
                    variant="contained"
                    sx={{ bgcolor: "var(--primary)", color: "var(--bg-base)", fontWeight: 800, px: 3, "&:hover": { bgcolor: "var(--primary)", opacity: 0.9 } }}
                  >
                    PLAN_SUBSCRIPTION
                  </Button>
                  <Button
                    component={Link}
                    href="/privacy"
                    variant="outlined"
                    sx={{ borderColor: "var(--border-subtle)", color: "var(--text-primary)", px: 3 }}
                  >
                    SECURITY_SPEC
                  </Button>
                </Stack>
              </Grid>

              <Grid item xs={12} md={6}>
                <Box sx={{ 
                  p: 3, 
                  bgcolor: "rgba(0,0,0,0.5)", 
                  borderRadius: 1, 
                  border: "1px solid var(--border-subtle)",
                  fontFamily: "var(--font-mono)"
                }}>
                  <Typography sx={{ fontSize: 10, color: "var(--text-faint)", mb: 2, textTransform: "uppercase", letterSpacing: "0.1em" }}>
                    // EMBED_PROMPT_v1.0
                  </Typography>
                  <Box component="pre" sx={{ fontSize: 12, color: "var(--primary)", overflowX: "auto", m: 0 }}>
{`<div data-graftai-embed data-user="OPERATIVE_ID"></div>
<script src="https://graftai.tech/relay.js" defer></script>`}
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </Box>
      </Container>
      <Footer />
    </Box>
  );
}
