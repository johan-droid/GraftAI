"use client";

import { Box, Chip, Container, LinearProgress, Paper, Skeleton, Stack, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { Loader2, Sparkles, CalendarDays, MessageSquare, ShieldCheck } from "lucide-react";

type LoadingVariant = "full" | "dashboard" | "auth";

interface AppLoadingScreenProps {
  title?: string;
  subtitle?: string;
  variant?: LoadingVariant;
}

const hintCards = [
  {
    icon: CalendarDays,
    title: "Syncing calendars",
    text: "Checking the latest availability and conflict data.",
  },
  {
    icon: MessageSquare,
    title: "Preparing copilots",
    text: "Loading the agent and chat context from the backend.",
  },
  {
    icon: ShieldCheck,
    title: "Verifying session",
    text: "Confirming your access and onboarding status.",
  },
];

function LoadingCard({ icon: Icon, title, text }: (typeof hintCards)[number]) {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        borderRadius: 4,
        background: "rgba(255,255,255,0.72)",
        border: "1px solid rgba(218,220,224,0.9)",
        boxShadow: "0 18px 40px -28px rgba(32,33,36,0.24)",
        backdropFilter: "blur(16px)",
      }}
    >
      <Stack direction="row" spacing={1.5} alignItems="flex-start">
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: 3,
            display: "grid",
            placeItems: "center",
            background: "linear-gradient(180deg, rgba(232,240,254,0.9), rgba(210,227,252,0.72))",
            color: "var(--primary)",
            flexShrink: 0,
          }}
        >
          <Icon size={18} />
        </Box>

        <Box sx={{ minWidth: 0, flex: 1 }}>
          <Typography sx={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>
            {title}
          </Typography>
          <Typography sx={{ mt: 0.5, fontSize: 12.5, lineHeight: 1.5, color: "var(--text-secondary)" }}>
            {text}
          </Typography>
        </Box>
      </Stack>
    </Paper>
  );
}

export function AppLoadingScreen({
  title = "Loading your workspace",
  subtitle = "Checking session state, onboarding progress, and live backend data.",
  variant = "full",
}: AppLoadingScreenProps) {
  const showCards = variant !== "auth";

  return (
    <Box
      sx={{
        minHeight: "100dvh",
        display: "grid",
        placeItems: "center",
        position: "relative",
        overflow: "hidden",
        background:
          "radial-gradient(circle at top left, rgba(26,115,232,0.14), transparent 28%), radial-gradient(circle at top right, rgba(52,168,83,0.1), transparent 24%), linear-gradient(180deg, #F8F9FA 0%, #FFFFFF 48%, #F8F9FA 100%)",
      }}
    >
      <Box aria-hidden sx={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
        <Box sx={{ position: "absolute", top: -120, left: -100, width: 260, height: 260, borderRadius: "50%", bgcolor: "rgba(26,115,232,0.10)", filter: "blur(90px)" }} />
        <Box sx={{ position: "absolute", right: -100, top: 120, width: 240, height: 240, borderRadius: "50%", bgcolor: "rgba(52,168,83,0.08)", filter: "blur(100px)" }} />
        <Box sx={{ position: "absolute", bottom: -140, left: "50%", width: 280, height: 280, borderRadius: "50%", bgcolor: "rgba(255,255,255,0.8)", filter: "blur(100px)", transform: "translateX(-50%)" }} />
      </Box>

      <Container maxWidth="lg" sx={{ position: "relative", zIndex: 1, py: { xs: 2, sm: 4, md: 6 } }}>
        <motion.div initial={{ opacity: 0, y: 16, scale: 0.985 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] as const }}>
          <Paper
            elevation={0}
            sx={{
              p: { xs: 2.5, sm: 3.5, md: 4.5 },
              borderRadius: { xs: 5, sm: 6 },
              background: "rgba(255,255,255,0.82)",
              border: "1px solid rgba(218,220,224,0.95)",
              boxShadow: "0 24px 60px -38px rgba(32,33,36,0.28)",
              backdropFilter: "blur(18px)",
            }}
          >
            <Stack spacing={3.25}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 4,
                    display: "grid",
                    placeItems: "center",
                    background: "linear-gradient(180deg, rgba(232,240,254,0.95), rgba(210,227,252,0.78))",
                    color: "var(--primary)",
                    flexShrink: 0,
                  }}
                >
                  <Loader2 size={22} className="animate-spin" />
                </Box>
                <Box>
                  <Chip
                    size="small"
                    icon={<Sparkles size={12} />}
                    label="GraftAI is preparing"
                    sx={{
                      height: 26,
                      borderRadius: 99,
                      backgroundColor: "rgba(26,115,232,0.08)",
                      color: "var(--primary)",
                      fontSize: 11,
                      fontWeight: 700,
                      letterSpacing: "0.08em",
                      textTransform: "uppercase",
                      mb: 1,
                      "& .MuiChip-icon": { color: "var(--primary)" },
                    }}
                  />
                  <Typography sx={{ fontSize: { xs: 22, sm: 28 }, fontWeight: 600, letterSpacing: "-0.03em", color: "var(--text-primary)", lineHeight: 1.1 }}>
                    {title}
                  </Typography>
                </Box>
              </Box>

              <Typography sx={{ fontSize: { xs: 14.5, sm: 15.5 }, lineHeight: 1.7, color: "var(--text-secondary)", maxWidth: 760 }}>
                {subtitle}
              </Typography>

              <Box>
                <LinearProgress
                  sx={{
                    height: 10,
                    borderRadius: 999,
                    backgroundColor: "rgba(26,115,232,0.08)",
                    "& .MuiLinearProgress-bar": {
                      borderRadius: 999,
                      background: "linear-gradient(90deg, #1A73E8 0%, #34A853 100%)",
                    },
                  }}
                />
              </Box>

              {showCards ? (
                <Box
                  sx={{
                    display: "grid",
                    gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" },
                    gap: 1.5,
                  }}
                >
                  {hintCards.map((card) => (
                    <LoadingCard key={card.title} {...card} />
                  ))}
                </Box>
              ) : (
                <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ pt: 0.5 }}>
                  <Skeleton variant="rounded" width={156} height={38} sx={{ borderRadius: 999 }} />
                  <Skeleton variant="rounded" width={120} height={38} sx={{ borderRadius: 999 }} />
                </Stack>
              )}
            </Stack>
          </Paper>
        </motion.div>
      </Container>
    </Box>
  );
}
