"use client";

import { Box, Button, Card, CardContent, Chip, Container, Divider, Grid, Stack, Typography } from "@mui/material";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  LayoutDashboard,
  ShieldCheck,
  Sparkles,
  TimerReset,
  Users,
} from "lucide-react";
import { Navigation } from "@/components/landing/Navigation";

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0 },
};

const stagger = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const metrics = [
  { label: "Setup steps", value: "4", note: "Profile to publish" },
  { label: "Backend sync", value: "Real time", note: "No mock data" },
  { label: "Responsive targets", value: "375 / 768 / 1024", note: "Mobile first" },
  { label: "Tone", value: "Minimal", note: "Readable by default" },
];

const featureCards = [
  {
    title: "Profile first",
    description: "Avatar, display name, bio, and phone live in one clean step with real API writes.",
    icon: Users,
  },
  {
    title: "Calendar sync",
    description: "Connect Google Calendar through the backend route that controls the onboarding flow.",
    icon: CalendarDays,
  },
  {
    title: "Availability rules",
    description: "Set timezone, work hours, and buffers without jumping between noisy screens.",
    icon: TimerReset,
  },
  {
    title: "Booking links",
    description: "Create event types and publish a simple public link that users can understand quickly.",
    icon: LayoutDashboard,
  },
];

const workflow = [
  {
    step: "01",
    title: "Profile",
    description: "Save identity, avatar, and profile preferences.",
  },
  {
    step: "02",
    title: "Calendar",
    description: "Connect the source of truth for availability.",
  },
  {
    step: "03",
    title: "Availability",
    description: "Set hours, timezone, and buffer rules.",
  },
  {
    step: "04",
    title: "Event type",
    description: "Publish the first booking link and share it.",
  },
];

const trustPills = ["JWT protected", "OAuth ready", "Backend sourced state", "Mobile friendly"];

const setupPreview = [
  { title: "Profile saved", detail: "Display name, bio, and avatar sync to the backend." },
  { title: "Calendar connected", detail: "OAuth starts from the real auth URL endpoint." },
  { title: "Availability ready", detail: "Timezone and work hours are stored centrally." },
];

function SectionLabel({ children }: { children: string }) {
  return (
    <Typography
      sx={{
        color: "var(--primary)",
        fontSize: 11,
        textTransform: "uppercase",
        letterSpacing: "0.2em",
        fontWeight: 800,
      }}
    >
      {children}
    </Typography>
  );
}

export default function Home() {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        position: "relative",
        overflow: "hidden",
        background:
          "radial-gradient(circle at 20% 15%, rgba(0,255,156,0.10), transparent 26%), radial-gradient(circle at 82% 18%, rgba(0,229,255,0.08), transparent 22%), linear-gradient(180deg, #070A0F 0%, #050608 100%)",
      }}
    >
      <Navigation />

      <Box component="main" sx={{ position: "relative", zIndex: 1, pt: { xs: 13, md: 16 }, pb: { xs: 8, md: 12 } }}>
        <Container maxWidth="xl">
          <Grid container spacing={{ xs: 5, md: 8 }} alignItems="center">
            <Grid item xs={12} lg={6}>
              <motion.div variants={stagger} initial="hidden" animate="visible">
                <Stack spacing={3}>
                  <motion.div variants={fadeUp}>
                    <Chip
                      icon={<Sparkles size={14} />}
                      label="Simplified scheduling for real teams"
                      variant="outlined"
                      sx={{
                        alignSelf: "flex-start",
                        borderColor: "rgba(255,255,255,0.10)",
                        color: "var(--text-primary)",
                        background: "rgba(255,255,255,0.03)",
                        fontWeight: 700,
                      }}
                    />
                  </motion.div>

                  <motion.div variants={fadeUp}>
                    <Typography
                      variant="h1"
                      sx={{
                        fontFamily: "var(--font-jakarta)",
                        fontSize: { xs: 40, sm: 54, lg: 68 },
                        lineHeight: 0.96,
                        fontWeight: 800,
                        letterSpacing: "-0.05em",
                        color: "var(--text-primary)",
                        maxWidth: 760,
                      }}
                    >
                      Scheduling that feels calm, clear, and finished.
                    </Typography>
                  </motion.div>

                  <motion.div variants={fadeUp}>
                    <Typography
                      sx={{
                        maxWidth: 680,
                        color: "var(--text-secondary)",
                        fontSize: { xs: 16, md: 18 },
                        lineHeight: 1.7,
                      }}
                    >
                      Connect calendars, set availability, and publish a booking link without digging through a crowded dashboard.
                    </Typography>
                  </motion.div>

                  <motion.div variants={fadeUp}>
                    <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                      <Button
                        component={Link}
                        href="/profile/setup"
                        variant="contained"
                        endIcon={<ArrowRight size={16} />}
                        sx={{
                          borderRadius: 999,
                          px: 3,
                          py: 1.35,
                          background: "linear-gradient(90deg, var(--primary), var(--secondary))",
                          color: "#04110b",
                          fontWeight: 800,
                          textTransform: "none",
                          boxShadow: "none",
                          "&:hover": { boxShadow: "0 10px 24px rgba(0,255,156,0.14)" },
                        }}
                      >
                        Start setup
                      </Button>
                      <Button
                        component={Link}
                        href="/dashboard"
                        variant="outlined"
                        startIcon={<LayoutDashboard size={16} />}
                        sx={{
                          borderRadius: 999,
                          px: 3,
                          py: 1.35,
                          borderColor: "rgba(255,255,255,0.12)",
                          color: "var(--text-primary)",
                          textTransform: "none",
                          fontWeight: 700,
                          "&:hover": { borderColor: "var(--primary)", background: "rgba(0,255,156,0.04)" },
                        }}
                      >
                        Open dashboard
                      </Button>
                    </Stack>
                  </motion.div>

                  <motion.div variants={fadeUp}>
                    <Stack direction="row" flexWrap="wrap" gap={1.25}>
                      {trustPills.map((pill) => (
                        <Chip
                          key={pill}
                          label={pill}
                          size="small"
                          variant="outlined"
                          sx={{
                            color: "var(--text-secondary)",
                            borderColor: "rgba(255,255,255,0.08)",
                            background: "rgba(255,255,255,0.02)",
                          }}
                        />
                      ))}
                    </Stack>
                  </motion.div>
                </Stack>
              </motion.div>
            </Grid>

            <Grid item xs={12} lg={6}>
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay: 0.08 }}>
                <Card
                  sx={{
                    borderRadius: 4,
                    border: "1px solid rgba(255,255,255,0.08)",
                    background: "rgba(10, 12, 16, 0.88)",
                    boxShadow: "0 30px 80px rgba(0,0,0,0.32)",
                  }}
                >
                  <CardContent sx={{ p: { xs: 3, md: 4 } }}>
                    <Stack spacing={3}>
                      <Stack direction="row" alignItems="flex-start" justifyContent="space-between" spacing={2}>
                        <Box>
                          <SectionLabel>Live setup preview</SectionLabel>
                          <Typography
                            sx={{
                              mt: 0.75,
                              fontFamily: "var(--font-jakarta)",
                              fontSize: { xs: 22, md: 28 },
                              fontWeight: 800,
                              letterSpacing: "-0.03em",
                            }}
                          >
                            Four steps to publish
                          </Typography>
                        </Box>
                        <Chip
                          label="Real endpoints"
                          size="small"
                          sx={{
                            background: "rgba(0,255,156,0.08)",
                            border: "1px solid rgba(0,255,156,0.16)",
                            color: "var(--primary)",
                            fontWeight: 700,
                          }}
                        />
                      </Stack>

                      <Box
                        sx={{
                          p: 2.5,
                          borderRadius: 3,
                          background: "rgba(255,255,255,0.03)",
                          border: "1px solid rgba(255,255,255,0.06)",
                        }}
                      >
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                          <Typography sx={{ fontSize: 14, fontWeight: 700 }}>Setup progress</Typography>
                          <Typography sx={{ fontSize: 12, color: "var(--text-muted)" }}>78% ready</Typography>
                        </Stack>
                        <Box
                          role="progressbar"
                          aria-valuemin={0}
                          aria-valuemax={100}
                          aria-valuenow={78}
                          aria-valuetext="Profile completion: 78%"
                          sx={{ mt: 1.5, height: 8, borderRadius: 999, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}
                        >
                          <Box sx={{ width: "78%", height: "100%", background: "linear-gradient(90deg, var(--primary), var(--secondary))" }} />
                        </Box>
                      </Box>

                      <Stack spacing={1.25}>
                        {setupPreview.map((item, index) => (
                          <Stack
                            key={item.title}
                            direction="row"
                            spacing={1.5}
                            alignItems="flex-start"
                            sx={{
                              p: 1.5,
                              borderRadius: 2.5,
                              border: "1px solid rgba(255,255,255,0.06)",
                              background: index === 0 ? "rgba(0,255,156,0.04)" : "rgba(255,255,255,0.02)",
                            }}
                          >
                            <CheckCircle2 size={18} color="var(--primary)" style={{ marginTop: 2, flexShrink: 0 }} />
                            <Box>
                              <Typography sx={{ fontWeight: 700, color: "var(--text-primary)" }}>{item.title}</Typography>
                              <Typography sx={{ fontSize: 13, color: "var(--text-secondary)", mt: 0.25 }}>{item.detail}</Typography>
                            </Box>
                          </Stack>
                        ))}
                      </Stack>

                      <Divider sx={{ borderColor: "rgba(255,255,255,0.08)" }} />

                      <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={2} alignItems={{ xs: "flex-start", sm: "center" }}>
                        <Box>
                          <Typography sx={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.18em", color: "var(--text-muted)", fontWeight: 700 }}>
                            Booking link
                          </Typography>
                          <Typography sx={{ mt: 0.5, fontSize: 15, color: "var(--text-primary)" }}>graftai.app/you</Typography>
                        </Box>
                        <Button
                          component={Link}
                          href="/profile/setup"
                          variant="contained"
                          endIcon={<ArrowRight size={16} />}
                          sx={{
                            borderRadius: 999,
                            px: 2.3,
                            py: 1.1,
                            background: "linear-gradient(90deg, var(--primary), var(--secondary))",
                            color: "#04110b",
                            fontWeight: 800,
                            textTransform: "none",
                          }}
                        >
                          Continue onboarding
                        </Button>
                      </Stack>
                    </Stack>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          </Grid>
        </Container>

        <Container maxWidth="xl" sx={{ mt: { xs: 6, md: 8 } }}>
          <Grid container spacing={2.5}>
            {metrics.map((metric) => (
              <Grid item xs={12} sm={6} lg={3} key={metric.label}>
                <Card
                  sx={{
                    height: "100%",
                    borderRadius: 4,
                    border: "1px solid rgba(255,255,255,0.08)",
                    background: "rgba(255,255,255,0.03)",
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Typography sx={{ fontSize: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.18em" }}>
                      {metric.label}
                    </Typography>
                    <Typography sx={{ mt: 1, fontFamily: "var(--font-jakarta)", fontSize: 30, fontWeight: 800, letterSpacing: "-0.04em" }}>
                      {metric.value}
                    </Typography>
                    <Typography sx={{ mt: 0.5, color: "var(--text-secondary)", fontSize: 14 }}>{metric.note}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      <Box id="product" sx={{ py: { xs: 8, md: 12 }, position: "relative" }}>
        <Container maxWidth="xl">
          <Stack spacing={1.5} sx={{ mb: 4, maxWidth: 760 }}>
            <SectionLabel>What it does</SectionLabel>
            <Typography
              sx={{
                fontFamily: "var(--font-jakarta)",
                fontSize: { xs: 30, md: 44 },
                fontWeight: 800,
                lineHeight: 1.06,
                letterSpacing: "-0.04em",
                color: "var(--text-primary)",
              }}
            >
              Simple surfaces for the parts people actually use.
            </Typography>
            <Typography sx={{ color: "var(--text-secondary)", maxWidth: 720, fontSize: { xs: 15, md: 16 } }}>
              The interface now emphasizes setup progress, booking links, and calendar sync instead of internal complexity.
            </Typography>
          </Stack>

          <Grid container spacing={2.5}>
            {featureCards.map((feature) => {
              const Icon = feature.icon;
              return (
                <Grid item xs={12} sm={6} lg={3} key={feature.title}>
                  <Card
                    sx={{
                      height: "100%",
                      borderRadius: 4,
                      border: "1px solid rgba(255,255,255,0.08)",
                      background: "rgba(255,255,255,0.03)",
                    }}
                  >
                    <CardContent sx={{ p: 3 }}>
                      <Box
                        sx={{
                          width: 44,
                          height: 44,
                          borderRadius: 2.5,
                          display: "grid",
                          placeItems: "center",
                          background: "rgba(0,255,156,0.08)",
                          border: "1px solid rgba(0,255,156,0.15)",
                        }}
                      >
                        <Icon size={20} color="var(--primary)" />
                      </Box>
                      <Typography sx={{ mt: 2, fontSize: 20, fontWeight: 800, letterSpacing: "-0.03em" }}>
                        {feature.title}
                      </Typography>
                      <Typography sx={{ mt: 1, color: "var(--text-secondary)", fontSize: 14.5, lineHeight: 1.7 }}>
                        {feature.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </Container>
      </Box>

      <Box
        id="workflow"
        sx={{
          py: { xs: 8, md: 12 },
          borderTop: "1px solid rgba(255,255,255,0.06)",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          background: "rgba(255,255,255,0.015)",
        }}
      >
        <Container maxWidth="xl">
          <Stack spacing={1.5} sx={{ mb: 4, maxWidth: 760 }}>
            <SectionLabel>Workflow</SectionLabel>
            <Typography
              sx={{
                fontFamily: "var(--font-jakarta)",
                fontSize: { xs: 28, md: 40 },
                fontWeight: 800,
                lineHeight: 1.06,
                letterSpacing: "-0.04em",
              }}
            >
              One flow, fewer decisions, faster setup.
            </Typography>
          </Stack>

          <Grid container spacing={2.5}>
            {workflow.map((item) => (
              <Grid item xs={12} sm={6} lg={3} key={item.step}>
                <Card
                  sx={{
                    height: "100%",
                    borderRadius: 4,
                    border: "1px solid rgba(255,255,255,0.08)",
                    background: "rgba(10,12,16,0.84)",
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Typography sx={{ color: "var(--primary)", fontSize: 12, fontWeight: 800, letterSpacing: "0.18em" }}>
                      {item.step}
                    </Typography>
                    <Typography sx={{ mt: 1, fontSize: 20, fontWeight: 800, letterSpacing: "-0.03em" }}>
                      {item.title}
                    </Typography>
                    <Typography sx={{ mt: 1, color: "var(--text-secondary)", fontSize: 14.5, lineHeight: 1.7 }}>
                      {item.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      <Box id="security" sx={{ py: { xs: 8, md: 12 } }}>
        <Container maxWidth="xl">
          <Grid container spacing={2.5} alignItems="stretch">
            <Grid item xs={12} md={7}>
              <Card
                sx={{
                  height: "100%",
                  borderRadius: 4,
                  border: "1px solid rgba(255,255,255,0.08)",
                  background: "rgba(10,12,16,0.84)",
                }}
              >
                <CardContent sx={{ p: { xs: 3, md: 4 } }}>
                  <SectionLabel>Integration</SectionLabel>
                  <Typography
                    sx={{
                      mt: 1,
                      fontFamily: "var(--font-jakarta)",
                      fontSize: { xs: 26, md: 36 },
                      fontWeight: 800,
                      lineHeight: 1.08,
                      letterSpacing: "-0.04em",
                    }}
                  >
                    Real endpoints, real auth, fewer sync gaps.
                  </Typography>
                  <Typography sx={{ mt: 2, color: "var(--text-secondary)", maxWidth: 640, fontSize: 15.5, lineHeight: 1.7 }}>
                    The UI points to the same backend routes that power profile setup, calendar connection, and event type creation.
                  </Typography>

                  <Stack direction="row" flexWrap="wrap" gap={1.25} sx={{ mt: 3 }}>
                    {[
                      "JWT protected",
                      "OAuth ready",
                      "Backend sourced state",
                      "Mobile first",
                    ].map((item) => (
                      <Chip
                        key={item}
                        icon={<ShieldCheck size={14} />}
                        label={item}
                        size="small"
                        variant="outlined"
                        sx={{
                          color: "var(--text-secondary)",
                          borderColor: "rgba(255,255,255,0.08)",
                          background: "rgba(255,255,255,0.02)",
                        }}
                      />
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={5}>
              <Card
                sx={{
                  height: "100%",
                  borderRadius: 4,
                  border: "1px solid rgba(255,255,255,0.08)",
                  background: "rgba(10,12,16,0.84)",
                }}
              >
                <CardContent sx={{ p: { xs: 3, md: 4 } }}>
                  <SectionLabel>Mobile first</SectionLabel>
                  <Typography
                    sx={{
                      mt: 1,
                      fontFamily: "var(--font-jakarta)",
                      fontSize: { xs: 24, md: 30 },
                      fontWeight: 800,
                      lineHeight: 1.08,
                      letterSpacing: "-0.04em",
                    }}
                  >
                    Readable on a phone, efficient on desktop.
                  </Typography>
                  <Typography sx={{ mt: 2, color: "var(--text-secondary)", fontSize: 15.5, lineHeight: 1.7 }}>
                    Spacing, tap targets, and copy are tuned for 375, 768, and 1024 pixel widths.
                  </Typography>

                  <Stack spacing={1.25} sx={{ mt: 3 }}>
                    {[
                      "Big tap targets",
                      "Short labels",
                      "Clear hierarchy",
                      "Single primary action",
                    ].map((item) => (
                      <Stack key={item} direction="row" spacing={1.25} alignItems="center">
                        <CheckCircle2 size={16} color="var(--primary)" />
                        <Typography sx={{ fontSize: 14.5, color: "var(--text-primary)" }}>{item}</Typography>
                      </Stack>
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Container>
      </Box>

      <Box id="pricing" sx={{ py: { xs: 8, md: 12 } }}>
        <Container maxWidth="xl">
          <Box
            sx={{
              borderRadius: 4,
              border: "1px solid rgba(255,255,255,0.08)",
              background: "linear-gradient(180deg, rgba(17,20,26,0.96), rgba(9,10,14,0.96))",
              p: { xs: 3, md: 5 },
            }}
          >
            <Stack spacing={3} alignItems="flex-start">
              <Chip
                label="Ready to ship"
                variant="outlined"
                sx={{ borderColor: "rgba(0,255,156,0.20)", color: "var(--primary)", background: "rgba(0,255,156,0.06)" }}
              />
              <Typography
                sx={{
                  fontFamily: "var(--font-jakarta)",
                  fontSize: { xs: 28, md: 42 },
                  fontWeight: 800,
                  lineHeight: 1.05,
                  letterSpacing: "-0.04em",
                  maxWidth: 920,
                }}
              >
                Start with the simplest flow. Keep the code and product in sync as you grow.
              </Typography>
              <Typography sx={{ color: "var(--text-secondary)", maxWidth: 760, fontSize: 15.5, lineHeight: 1.7 }}>
                We can keep refining onboarding, the landing page, and the backend contract phase by phase until the app feels polished everywhere.
              </Typography>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <Button
                  component={Link}
                  href="/profile/setup"
                  variant="contained"
                  endIcon={<ArrowRight size={16} />}
                  sx={{
                    borderRadius: 999,
                    px: 3,
                    py: 1.35,
                    background: "linear-gradient(90deg, var(--primary), var(--secondary))",
                    color: "#04110b",
                    fontWeight: 800,
                    textTransform: "none",
                    boxShadow: "none",
                  }}
                >
                  Continue setup
                </Button>
                <Button
                  component={Link}
                  href="/dashboard"
                  variant="outlined"
                  sx={{
                    borderRadius: 999,
                    px: 3,
                    py: 1.35,
                    borderColor: "rgba(255,255,255,0.12)",
                    color: "var(--text-primary)",
                    textTransform: "none",
                    fontWeight: 700,
                    "&:hover": { borderColor: "var(--primary)", background: "rgba(0,255,156,0.04)" },
                  }}
                >
                  Go to dashboard
                </Button>
              </Stack>
            </Stack>
          </Box>
        </Container>
      </Box>

      <Box component="footer" sx={{ py: 4, borderTop: "1px solid rgba(255,255,255,0.08)" }}>
        <Container maxWidth="xl">
          <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" gap={2} alignItems={{ xs: "flex-start", sm: "center" }}>
            <Typography sx={{ color: "var(--text-muted)", fontSize: 14 }}>
              GraftAI · scheduling that stays readable.
            </Typography>
            <Stack direction="row" spacing={2.5} flexWrap="wrap">
              <Button component={Link} href="/login" variant="text" sx={{ color: "var(--text-secondary)", textTransform: "none", minWidth: "auto" }}>
                Login
              </Button>
              <Button component={Link} href="/profile/setup" variant="text" sx={{ color: "var(--text-secondary)", textTransform: "none", minWidth: "auto" }}>
                Profile setup
              </Button>
              <Button component={Link} href="/dashboard" variant="text" sx={{ color: "var(--text-secondary)", textTransform: "none", minWidth: "auto" }}>
                Dashboard
              </Button>
            </Stack>
          </Stack>
        </Container>
      </Box>
    </Box>
  );
}
