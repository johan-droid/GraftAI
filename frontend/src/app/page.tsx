"use client";

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { 
  Box, 
  Button, 
  Card, 
  CardContent, 
  Chip, 
  Container, 
  Divider, 
  Grid, 
  Stack, 
  Typography,
  alpha,
  TextField,
  Alert,
  SxProps,
  Theme
} from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  ArrowRight,
  CalendarDays,
  ShieldCheck,
  Sparkles,
  TimerReset,
  Users,
  Activity,
  UserCheck,
  UserMinus,
  Globe,
  Quote,
  ChevronRight
} from "lucide-react";

import { Navigation } from "@/components/landing/Navigation";
import { useTheme } from "@/contexts/ThemeContext";
import DotField from "@/components/landing/DotField";
import "@/components/landing/DotField.css";

// Animation variants
const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.8,
      ease: [0.22, 1, 0.36, 1] as const
    }
  },
};

const stagger = {
  visible: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

// Types
interface Stats {
  registered_users: number;
  live_visitors: number;
  deleted_accounts: number;
}

interface FeatureCard {
  title: string;
  description: string;
  icon: React.ComponentType<{ size: number }>;
  color: string;
}

const FEATURE_CARDS: FeatureCard[] = [
  {
    title: "AI Orchestration",
    description: "Intelligent scheduling that learns your team's rhythm and optimizes for deep work.",
    icon: Sparkles,
    color: "#1a73e8", // Google Blue
  },
  {
    title: "Calendar Harmony",
    description: "Seamless synchronization across Google, Outlook, and specialized industry tools.",
    icon: CalendarDays,
    color: "#34a853", // Google Green
  },
  {
    title: "Dynamic Availability",
    description: "Complex rule-based slots that adapt to your changing timezone and workload.",
    icon: TimerReset,
    color: "#fbbc04", // Google Yellow
  },
  {
    title: "Enterprise Security",
    description: "JWT-protected endpoints and OAuth2 standard flows built for scale.",
    icon: ShieldCheck,
    color: "#ea4335", // Google Red
  },
];

function SectionLabel({ 
  children, 
  color = "var(--brand-primary)" 
}: { 
  children: string; 
  color?: string 
}) {
  return (
    <Typography
      component="div"
      role="doc-subtitle"
      sx={{
        color: color,
        fontSize: 12,
        textTransform: "uppercase",
        letterSpacing: "0.15em",
        fontWeight: 700,
        mb: 2,
        display: "flex",
        alignItems: "center",
        gap: 1
      }}
    >
      <Box 
        aria-hidden="true"
        sx={{ width: 12, height: 2, bgcolor: color, borderRadius: 1 }} 
      />
      {children}
    </Typography>
  );
}

function SpotlightCard({ 
  children, 
  sx = {}, 
  color = "#1a73e8" 
}: { 
  children: React.ReactNode; 
  sx?: SxProps<Theme>; 
  color?: string 
}) {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <Card
      onMouseMove={handleMouseMove}
      className="spotlight-card"
      sx={{
        ...sx,
        "--mouse-x": `${mousePos.x}px`,
        "--mouse-y": `${mousePos.y}px`,
        position: "relative",
        overflow: "hidden",
        "&::before": {
          background: `radial-gradient(400px circle at var(--mouse-x) var(--mouse-y), ${alpha(color, 0.08)}, transparent 40%)`
        }
      }}
    >
      {children}
    </Card>
  );
}

function HeroBackground() {
  return (
    <Box
      sx={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        height: "100vh",
        zIndex: 0,
        overflow: "hidden",
        pointerEvents: "none",
      }}
    >
      <motion.div
        animate={{
          x: [0, 40, 0],
          y: [0, 20, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear",
        }}
        style={{
          position: "absolute",
          top: "-10%",
          left: "20%",
          width: "60vw",
          height: "60vw",
          background: "radial-gradient(circle, rgba(26, 115, 232, 0.03) 0%, transparent 70%)",
          filter: "blur(80px)",
        }}
      />
      <motion.div
        animate={{
          x: [0, -18, 0],
          y: [0, -10, 0],
        }}
        transition={{
          duration: 28,
          repeat: Infinity,
          ease: "linear",
        }}
        style={{
          position: "absolute",
          bottom: "10%",
          right: "10%",
          width: "42vw",
          height: "42vw",
          background: "radial-gradient(circle, rgba(52, 168, 83, 0.016) 0%, transparent 68%)",
          filter: "blur(80px)",
        }}
      />
    </Box>
  );
}

function DraggableWidget({ 
  children, 
  initial = {}, 
  sx = {} 
}: { 
  children: React.ReactNode; 
  initial?: Record<string, unknown>; 
  sx?: SxProps<Theme>; 
}) {
  return (
    <motion.div
      drag
      dragConstraints={{ left: -50, right: 50, top: -50, bottom: 50 }}
      whileDrag={{ scale: 1.05, zIndex: 50 }}
      initial={{ opacity: 0, y: 40, ...initial }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ type: "spring", damping: 20, stiffness: 100 }}
      style={{ cursor: "grab" }}
    >
      <Box 
        sx={{ 
          bgcolor: "var(--bg-base)", 
          border: "1px solid var(--border-subtle)", 
          borderRadius: 6,
          boxShadow: "0 12px 40px rgba(0,0,0,0.06)",
          p: 3,
          ...sx 
        }}
      >
        {children}
      </Box>
    </motion.div>
  );
}

function MobileAppShowcase() {
  return (
    <Box component="section" sx={{ py: { xs: 12, md: 15 }, position: "relative", zIndex: 2 }}>
      <Container maxWidth="md">
        <Stack spacing={4} alignItems="center" textAlign="center" sx={{ mb: 10 }}>
          <SectionLabel color="#4285F4">Infrastructure</SectionLabel>
          <Typography component="h2" variant="h2" sx={{ fontSize: { xs: 32, md: 48 }, fontWeight: 800, color: "var(--text-primary)", letterSpacing: "-0.04em" }}>
            The app-native experience.
          </Typography>
          <Typography sx={{ color: "rgba(15, 23, 42, 0.74)", maxWidth: 600, fontSize: { xs: 16, md: 18 } }}>
            Interact with our scheduling core directly. These widgets power the engine beneath GraftAI.
          </Typography>
        </Stack>

        <Box sx={{ position: "relative", height: 500, width: "100%", display: "flex", justifyContent: "center" }}>
          {/* Calendar Widget */}
          <DraggableWidget sx={{ width: 320, position: "absolute", left: { xs: 0, md: -60 }, top: 0 }}>
            <Stack spacing={2}>
              <Stack direction="row" justifyContent="space-between">
                <Typography sx={{ fontWeight: 800, fontSize: 14 }}>March 2026</Typography>
                <ChevronRight size={16} aria-hidden="true" />
              </Stack>
              <Box sx={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 1 }}>
                {[...Array(31)].map((_, i) => (
                  <Box 
                    key={i} 
                    aria-label={`March ${i + 1}, ${i === 15 ? "selected" : "available"}`}
                    sx={{ 
                      width: 28, height: 28, 
                      borderRadius: 1.5, 
                      bgcolor: i === 15 ? "var(--brand-primary)" : "var(--bg-surface)",
                      color: i === 15 ? "white" : "inherit",
                      display: "grid", placeItems: "center",
                      fontSize: 10, fontWeight: 700
                    }}
                  >
                    {i + 1}
                  </Box>
                ))}
              </Box>
            </Stack>
          </DraggableWidget>

          {/* Booking Widget */}
          <DraggableWidget sx={{ width: 280, position: "absolute", right: { xs: 0, md: -40 }, top: 80 }}>
            <Stack spacing={3}>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <Box sx={{ width: 32, height: 32, borderRadius: "50%", bgcolor: "#EA4335", color: "white", display: "grid", placeItems: "center", fontSize: 12, fontWeight: 800 }} aria-label="Jason Smith's avatar">JS</Box>
                <Box>
                  <Typography sx={{ fontWeight: 700, fontSize: 13 }}>Jason Smith</Typography>
                  <Typography sx={{ fontSize: 10, color: "rgba(15, 23, 42, 0.72)" }}>Product Design</Typography>
                </Box>
              </Stack>
              <Typography sx={{ fontSize: 14, fontWeight: 600, color: "rgba(15, 23, 42, 0.84)" }}>Sync: Design Review</Typography>
              <Button fullWidth variant="contained" sx={{ bgcolor: "#4285F4", borderRadius: 2, py: 1, textTransform: "none", fontSize: 12 }}>
                Confirm Slot
              </Button>
            </Stack>
          </DraggableWidget>

          {/* Availability Overlay Widget (Cal-inspired) */}
          <DraggableWidget sx={{ width: 220, position: "absolute", bottom: -20, right: { xs: 0, md: "15%" } }}>
            <Stack spacing={2}>
              <Typography sx={{ fontWeight: 800, fontSize: 13 }}>Overlay availability</Typography>
              <Stack spacing={1}>
                {[
                  { name: "My Calendar", color: "#4285F4" },
                  { name: "Engineering", color: "#34A853" }
                ].map(item => (
                  <Stack key={item.name} direction="row" alignItems="center" spacing={1}>
                    <Box 
                      sx={{ width: 10, height: 10, borderRadius: "50%", bgcolor: item.color }} 
                      aria-label={`${item.name} indicator`}
                      aria-hidden="true"
                    />
                    <Typography sx={{ fontSize: 11, fontWeight: 600 }}>{item.name}</Typography>
                  </Stack>
                ))}
              </Stack>
              <Box sx={{ p: 1, bgcolor: alpha("#4285F4", 0.05), borderRadius: 1.5, border: "1px dashed #4285F4" }}>
                <Typography sx={{ fontSize: 10, color: "#4285F4", fontWeight: 700 }}>3 slots match all</Typography>
              </Box>
            </Stack>
          </DraggableWidget>

          {/* Sync Success Widget */}
          <DraggableWidget sx={{ width: 240, position: "absolute", bottom: 40, left: "20%" }}>
            <Stack direction="row" spacing={2} alignItems="center">
              <Box sx={{ width: 40, height: 40, borderRadius: 2, bgcolor: alpha("#34A853", 0.1), color: "#34A853", display: "grid", placeItems: "center" }} aria-hidden="true">
                <ShieldCheck size={20} />
              </Box>
              <Box>
                <Typography sx={{ fontWeight: 800, fontSize: 13, color: "#34A853" }}>Context Synced</Typography>
                <Typography sx={{ fontSize: 11, color: "rgba(15, 23, 42, 0.72)" }}>Zero conflicts found</Typography>
              </Box>
            </Stack>
          </DraggableWidget>

          {/* The "Phone" frame (Abstract) */}
          <Box 
            aria-hidden="true"
            sx={{ 
              width: 320, 
              height: "100%", 
              bgcolor: "var(--bg-surface)", 
              borderRadius: 10, 
              border: "8px solid var(--border-subtle)", 
              opacity: 0.3,
              zIndex: -1
            }} 
          />
        </Box>
      </Container>
    </Box>
  );
}
function OrchestrationLogs() {
  const [logs, setLogs] = useState<string[]>([]);
  const possibleLogs = useMemo(() => [
    "[INFO] Context synchronized",
    "[DEBUG] Analyzing calendar drift...",
    "[SUCCESS] Conflict resolved: 14:00 UTC",
    "[INFO] GraftAI Mode: Optimizing focus...",
    "[SYSTEM] Entropy balanced",
    "[LLM] Gemini 1.5 Pro: Token usage within limits",
    "[EVENT] User 'Marcus' joined live stream",
    "[INFO] Heartbeat acknowledged"
  ], []);

  useEffect(() => {
    const interval = setInterval(() => {
      const nextLog = possibleLogs[Math.floor(Math.random() * possibleLogs.length)];
      setLogs(prev => [...prev.slice(-4), nextLog]);
    }, 3000);
    return () => clearInterval(interval);
  }, [possibleLogs]);

  return (
    <Box 
      component="aside"
      role="status"
      aria-label="System orchestration logs"
      aria-live="polite"
      sx={{ 
        fontFamily: "var(--font-mono)", 
        fontSize: 10, 
        color: alpha("#1a73e8", 0.6),
        borderLeft: `1px solid ${alpha("#1a73e8", 0.2)}`,
        pl: 2,
        mt: 4,
        display: "flex",
        flexDirection: "column",
        gap: 0.5,
        minHeight: 60,
        opacity: 0.8
      }}
    >
      <AnimatePresence mode="popLayout">
        {logs.map((log, i) => (
          <motion.div
            key={`${log}-${i}`}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            transition={{ duration: 0.4 }}
          >
            {log}
          </motion.div>
        ))}
      </AnimatePresence>
    </Box>
  );
}

function CounterCard({ 
  label, 
  value, 
  icon: Icon, 
  color, 
  subValue 
}: { 
  label: string; 
  value: number; 
  icon: React.ComponentType<{ size: number }>; 
  color: string; 
  subValue?: string 
}) {
  return (
    <Card
      sx={{
        height: "100%",
        borderRadius: 6,
        border: "1px solid var(--border-subtle)",
        bgcolor: "var(--bg-base)",
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        "&:hover": {
          transform: "translateY(-6px)",
          boxShadow: "var(--shadow-elevated)",
          borderColor: alpha(color, 0.2),
        }
      }}
    >
      <CardContent sx={{ p: 4 }}>
        <Stack direction="row" spacing={2.5} alignItems="flex-start">
          <Box
            sx={{
              width: 54,
              height: 54,
              borderRadius: 4,
              display: "grid",
              placeItems: "center",
              background: alpha(color, 0.08),
              color: color,
            }}
            aria-hidden="true"
          >
            <Icon size={26} />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography 
              sx={{ 
                fontSize: 13, 
                color: "rgba(15, 23, 42, 0.72)", 
                fontWeight: 600, 
                mb: 0.5 
              }}
            >
              {label}
            </Typography>
            <Stack direction="row" alignItems="baseline" spacing={1}>
              <Typography 
                aria-label={`${label}: ${value.toLocaleString()}`}
                sx={{ 
                  fontSize: 36, 
                  fontWeight: 800, 
                  color: "var(--text-primary)", 
                  letterSpacing: "-0.02em" 
                }}
              >
                {value.toLocaleString()}
              </Typography>
              {subValue && (
                <Typography 
                  aria-label={`Change: ${subValue}`}
                  sx={{ 
                    fontSize: 13, 
                    color: "var(--semantic-success)", 
                    fontWeight: 600 
                  }}
                >
                  {subValue}
                </Typography>
              )}
            </Stack>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function Home() {
  const { setMode } = useTheme();
  const [stats, setStats] = useState<Stats>({ registered_users: 0, live_visitors: 0, deleted_accounts: 0 });
  const [sessionId] = useState(() => typeof window !== "undefined" ? (localStorage.getItem("graftai_session") || crypto.randomUUID()) : "");
  const [emailInput, setEmailInput] = useState("");
  const [emailError, setEmailError] = useState("");
  const [emailSuccess, setEmailSuccess] = useState(false);
  const [isSubmittingEmail, setIsSubmittingEmail] = useState(false);
  const emailInputRef = useRef<HTMLInputElement>(null);

  // Email validation regex
  const isValidEmail = useCallback((email: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }, []);

  const handleEmailSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setEmailError("");
    setEmailSuccess(false);

    if (!emailInput.trim()) {
      setEmailError("Email is required");
      return;
    }

    if (!isValidEmail(emailInput)) {
      setEmailError("Please enter a valid email address");
      return;
    }

    setIsSubmittingEmail(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/public/newsletter/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailInput.trim() })
      });

      if (response.ok) {
        setEmailSuccess(true);
        setEmailInput("");
        setTimeout(() => setEmailSuccess(false), 5000);
      } else {
        const error = await response.json().catch(() => ({}));
        setEmailError(error.detail || "Failed to subscribe. Please try again.");
      }
    } catch {
      setEmailError("Network error. Please try again later.");
    } finally {
      setIsSubmittingEmail(false);
    }
  }, [emailInput, isValidEmail]);

  useEffect(() => {
    setMode("light");

    if (typeof window !== "undefined") {
      localStorage.setItem("graftai_session", sessionId);
    }

    const fetchStats = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/public/stats`);
        if (res.ok) {
          const data: Stats = await res.json();
          setStats(data);
        }
      } catch {
        if (process.env.NODE_ENV === 'development') {
          console.log("📊 [Dev Mode] Stats unavailable - Backend offline");
        }
      }
    };

    const sendHeartbeat = async () => {
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/public/heartbeat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId })
        });
      } catch {
        // Silent fail for heartbeat
      }
    };

    fetchStats();
    sendHeartbeat();

    const statsInterval = setInterval(fetchStats, 10000);
    const heartbeatInterval = setInterval(sendHeartbeat, 60000);

    return () => {
      clearInterval(statsInterval);
      clearInterval(heartbeatInterval);
    };
  }, [setMode, sessionId]);

  return (
    <Box sx={{ bgcolor: "var(--bg-base)", minHeight: "100vh", position: "relative", overflow: "hidden" }} className="bg-dot-grid">
      {/* DotField animated background */}
      <Box sx={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        zIndex: 1,
        pointerEvents: "none",
        opacity: 0.18
      }}>
        <DotField
          dotRadius={2}
          dotSpacing={24}
          bulgeStrength={45}
          glowRadius={110}
          sparkle={false}
          waveAmplitude={0}
          style={{ width: "100%", height: "100%" }}
        />
      </Box>
      {/* End DotField */}
      <Box sx={{ position: "relative", zIndex: 2 }}>
        <HeroBackground />
        <Navigation />

      {/* Hero Section */}
      <Box component="main" sx={{ pt: { xs: 12, sm: 15, md: 24 }, pb: { xs: 10, md: 16 } }}>
        <Container maxWidth="lg">
          <motion.div variants={stagger} initial="hidden" animate="visible">
            <Stack spacing={4} alignItems="center" textAlign="center">
              <motion.div variants={fadeUp}>
                <Chip
                  icon={<Box sx={{ width: 8, height: 8, borderRadius: "50%", bgcolor: "var(--semantic-success)", animation: "pulse 2s infinite" }} />}
                  label="GraftAI Mode: Active"
                  sx={{
                    bgcolor: alpha("#1a73e8", 0.05),
                    color: "#1a73e8",
                    fontWeight: 800,
                    px: 1.5,
                    py: 2.5,
                    border: "1px solid",
                    borderColor: alpha("#1a73e8", 0.1),
                    borderRadius: 99,
                    fontSize: 12,
                    textTransform: "uppercase",
                    letterSpacing: "0.1em"
                  }}
                />
              </motion.div>

              <motion.div variants={fadeUp}>
                <Typography
                  component="h1"
                  variant="h1"
                  sx={{
                    fontSize: { xs: 42, sm: 56, md: 80 },
                    fontWeight: 800,
                    lineHeight: 1.05,
                    letterSpacing: "-0.05em",
                    color: "var(--text-primary)",
                    maxWidth: 900,
                    fontFamily: "var(--font-sans)",
                    "& span": { display: "inline-block" }
                  }}
                >
                  <Box component="span" sx={{ color: "#4285F4" }}>Scheduling infrastructure</Box>{" "}
                  <span>for</span>{" "}
                  <Box component="span" sx={{ color: "#34A853" }}>modern teams.</Box>
                </Typography>
              </motion.div>

              <motion.div variants={fadeUp}>
                <Typography
                  component="p"
                  sx={{
                    maxWidth: 720,
                    color: "rgba(15, 23, 42, 0.78)",
                    fontSize: { xs: 16, sm: 18, md: 22 },
                    lineHeight: 1.6,
                    fontWeight: 500
                  }}
                >
                  The AI-native scheduling engine that keeps calendars conflict-free, protects deep work, and adapts across every tool.
                </Typography>
              </motion.div>

              <motion.div variants={fadeUp}>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={2.5} sx={{ width: { xs: "100%", sm: "auto" } }}>
                  <Button
                    component={Link}
                    href="/profile/setup"
                    variant="contained"
                    size="large"
                    endIcon={<ArrowRight size={20} />}
                    sx={{
                      borderRadius: 99,
                      px: 5,
                      py: 2.2,
                      fontSize: { xs: 15, md: 17 },
                      fontWeight: 800,
                      bgcolor: "var(--brand-primary)",
                      "&:hover": { bgcolor: "var(--brand-primary-light)", boxShadow: "var(--shadow-glow)" },
                      textTransform: "none",
                      letterSpacing: "-0.01em",
                      width: { xs: "100%", sm: "auto" }
                    }}
                  >
                    Get started with GraftAI
                  </Button>
                  <Button
                    component={Link}
                    href="/dashboard"
                    variant="outlined"
                    size="large"
                    sx={{
                      borderRadius: 99,
                      px: 5,
                      py: 2.2,
                      fontSize: { xs: 15, md: 17 },
                      fontWeight: 700,
                      borderColor: "var(--border-subtle)",
                      color: "var(--text-primary)",
                      "&:hover": { bgcolor: "var(--bg-surface)", borderColor: "var(--brand-primary)" },
                      textTransform: "none",
                      width: { xs: "100%", sm: "auto" }
                    }}
                  >
                    Explore the engine
                  </Button>
                </Stack>
              </motion.div>

              <motion.div variants={fadeUp}>
                <OrchestrationLogs />
              </motion.div>
            </Stack>
          </motion.div>
        </Container>
      </Box>

      <MobileAppShowcase />

      {/* Stats Section */}
      <Box component="section" sx={{ py: 10, bgcolor: "var(--bg-surface)", borderY: "1px solid var(--border-subtle)" }}>
        <Container maxWidth="lg">
          <SectionLabel color="#1a73e8">Real-time Platform Activity</SectionLabel>
          <Grid container spacing={4} role="list">
            <Grid item xs={12} md={4} role="listitem">
              <CounterCard 
                label="Registered Users" 
                value={stats.registered_users} 
                icon={UserCheck} 
                color="#1a73e8" 
                subValue="+12% this week"
              />
            </Grid>
            <Grid item xs={12} md={4} role="listitem">
              <Box sx={{ position: "relative" }}>
                <CounterCard 
                  label="Live Tracking" 
                  value={stats.live_visitors} 
                  icon={Activity} 
                  color="#34a853" 
                />
                <Box 
                  aria-hidden="true"
                  sx={{ 
                    position: "absolute", top: 16, right: 16, width: 10, height: 10, 
                    borderRadius: "50%", bgcolor: "var(--semantic-success)",
                    animation: "pulse 2s infinite" 
                  }} 
                />
              </Box>
            </Grid>
            <Grid item xs={12} md={4} role="listitem">
              <CounterCard 
                label="Accounts Closed" 
                value={stats.deleted_accounts} 
                icon={UserMinus} 
                color="#ea4335" 
              />
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Feature Grid - Mobile Focused */}
      <Box component="section" id="product" sx={{ py: { xs: 12, md: 24 } }}>
        <Container maxWidth="md">
          <Stack spacing={8}>
            <Box textAlign="center">
              <SectionLabel color="#34a853">Features</SectionLabel>
              <Typography component="h2" variant="h2" sx={{ fontSize: { xs: 32, md: 48 }, fontWeight: 800, color: "var(--text-primary)", letterSpacing: "-0.04em", mb: 2 }}>
                High-performance scheduling.
              </Typography>
              <Typography sx={{ color: "rgba(15, 23, 42, 0.74)", fontSize: { xs: 16, md: 18 }, maxWidth: 500, mx: "auto" }}>
                Everything you need to orchestrate focus and availability.
              </Typography>
            </Box>

            <Grid container spacing={2} role="list">
              {FEATURE_CARDS.map((feature, i) => (
                <Grid item xs={12} sm={6} key={feature.title} role="listitem">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    viewport={{ once: true }}
                    style={{ height: "100%" }}
                  >
                    <SpotlightCard
                      color={feature.color}
                      sx={{
                        height: "100%",
                        borderRadius: 6,
                        border: "1px solid var(--border-subtle)",
                        bgcolor: "var(--bg-base)",
                        transition: "all 0.3s ease",
                        "&:hover": {
                          boxShadow: "var(--shadow-elevated)",
                        },
                        "&::after": {
                          content: '""',
                          position: "absolute",
                          top: 0, left: 0, width: 4, height: "100%",
                          bgcolor: feature.color
                        }
                      }}
                    >
                      <CardContent sx={{ p: 4, position: "relative", zIndex: 1 }}>
                        <Stack spacing={2}>
                          <Box sx={{ color: feature.color }} aria-hidden="true">
                            <feature.icon size={28} />
                          </Box>
                          <Typography component="h3" sx={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>
                            {feature.title}
                          </Typography>
                          <Typography sx={{ color: "rgba(15, 23, 42, 0.72)", lineHeight: 1.7, fontSize: 14 }}>
                            {feature.description}
                          </Typography>
                        </Stack>
                      </CardContent>
                    </SpotlightCard>
                  </motion.div>
                </Grid>
              ))}
            </Grid>
          </Stack>
        </Container>
      </Box>

      {/* Social Proof / Logo Cloud */}
      <Box sx={{ py: 10, borderTop: "1px solid var(--border-subtle)", opacity: 0.6 }}>
        <Container maxWidth="lg">
          <Typography textAlign="center" sx={{ color: "var(--text-muted)", fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.2em", mb: 6 }}>
            Trusted by developers from
          </Typography>
          <Grid container spacing={4} justifyContent="center" alignItems="center">
            {['Vercel', 'Stripe', 'Supabase', 'Railway', 'Neon'].map((name) => (
              <Grid item xs={6} sm={4} md={2} key={name} textAlign="center">
                <Typography variant="h6" sx={{ color: "var(--text-primary)", fontWeight: 800, opacity: 0.5, filter: "grayscale(100%)" }}>
                  {name}
                </Typography>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Testimonials */}
      <Box component="section" sx={{ py: { xs: 12, md: 20 }, bgcolor: alpha("#1a73e8", 0.02) }}>
        <Container maxWidth="lg">
          <Stack spacing={8}>
            <Box textAlign="center">
              <SectionLabel color="#fbbc04">Testimonials</SectionLabel>
              <Typography component="h2" variant="h2" sx={{ fontSize: { xs: 36, md: 54 }, fontWeight: 800, color: "var(--text-primary)", letterSpacing: "-0.04em" }}>
                What pioneers say.
              </Typography>
            </Box>

            <Grid container spacing={4} role="list">
              {[
                {
                  quote: "GraftAI completely eliminated our team's scheduling conflicts. It's like having a chief of staff for every engineer.",
                  author: "Sarah Chen",
                  role: "CTO at TechFlow",
                  avatar: "SC"
                },
                {
                  quote: "The cleanest calendar interface I've ever used. The AI orchestration is surprisingly accurate.",
                  author: "Marcus Thorne",
                  role: "Lead Developer, Nimbus",
                  avatar: "MT"
                }
              ].map((t, i) => (
                <Grid item xs={12} md={6} key={i} role="listitem">
                  <Card 
                    sx={{ 
                      p: { xs: 4, md: 5 }, 
                      borderRadius: 8, 
                      height: "100%", 
                      border: "1px solid var(--border-subtle)", 
                      bgcolor: "var(--bg-base)",
                      transition: "all 0.3s ease",
                      "&:hover": {
                        boxShadow: "var(--shadow-elevated)",
                        transform: "translateY(-4px)"
                      }
                    }}
                  >
                    <Stack spacing={4}>
                      <Quote size={40} color={alpha("#1a73e8", 0.1)} aria-hidden="true" />
                      <blockquote>
                        <Typography sx={{ fontSize: { xs: 16, md: 20 }, fontStyle: "italic", color: "var(--text-primary)", lineHeight: 1.6, m: 0 }}>
                          &ldquo;{t.quote}&rdquo;
                        </Typography>
                      </blockquote>
                      <Stack direction="row" spacing={2} alignItems="center">
                        <Box 
                          sx={{ 
                            width: 48, 
                            height: 48, 
                            borderRadius: "50%", 
                            bgcolor: "var(--brand-primary)", 
                            color: "white", 
                            display: "grid", 
                            placeItems: "center", 
                            fontWeight: 800,
                            fontSize: 12
                          }}
                          aria-label={`${t.author}'s avatar`}
                        >
                          {t.avatar}
                        </Box>
                        <Box>
                          <Typography sx={{ fontWeight: 800, color: "rgba(15, 23, 42, 0.96)", fontSize: 15 }}>{t.author}</Typography>
                          <Typography sx={{ fontSize: 13, color: "rgba(15, 23, 42, 0.68)" }}>{t.role}</Typography>
                        </Box>
                      </Stack>
                    </Stack>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Stack>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box component="section" sx={{ py: { xs: 12, md: 15 } }}>
        <Container maxWidth="md">
          <Card 
            sx={{ 
              borderRadius: 10, 
              bgcolor: "var(--text-primary)", 
              color: "var(--bg-base)",
              p: { xs: 6, md: 10 },
              textAlign: "center",
              overflow: "hidden",
              position: "relative"
            }}
          >
            <Box sx={{ position: "absolute", top: -100, right: -100, width: 300, height: 300, bgcolor: alpha("#1a73e8", 0.1), borderRadius: "50%", filter: "blur(60px)" }} aria-hidden="true" />
            <Stack spacing={4} alignItems="center">
              <Typography component="h2" variant="h2" sx={{ fontSize: { xs: 32, md: 48 }, fontWeight: 800, lineHeight: 1.1, letterSpacing: "-0.03em" }}>
                Ready to reclaim your calendar?
              </Typography>
              <Typography sx={{ opacity: 0.8, fontSize: { xs: 16, md: 18 }, maxWidth: 500 }}>
                Join the thousands of developers and teams scaling their time with GraftAI.
              </Typography>
              <Button
                component={Link}
                href="/profile/setup"
                variant="contained"
                size="large"
                sx={{
                  bgcolor: "white",
                  color: "black",
                  borderRadius: 99,
                  px: 6,
                  py: 2,
                  fontWeight: 800,
                  fontSize: 18,
                  "&:hover": { bgcolor: "#f1f3f4" }
                }}
              >
                View Demo
              </Button>
              <motion.div variants={fadeUp}>
                <OrchestrationLogs />
              </motion.div>
            </Stack>
          </Card>
        </Container>
      </Box>

      {/* Footer */}
      <Box component="footer" sx={{ py: 12, borderTop: "1px solid var(--border-subtle)", bgcolor: "var(--bg-base)" }}>
        <Container maxWidth="lg">
          <Grid container spacing={8}>
            <Grid item xs={12} md={4}>
              <Stack spacing={3}>
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Box sx={{ width: 32, height: 32, bgcolor: "var(--brand-primary)", borderRadius: 1.5, display: "grid", placeItems: "center" }}>
                    <Sparkles size={18} color="white" aria-hidden="true" />
                  </Box>
                  <Typography component="h3" variant="h6" sx={{ fontWeight: 800, letterSpacing: "-0.02em" }}>GraftAI</Typography>
                </Stack>
                <Typography sx={{ color: "rgba(15, 23, 42, 0.74)", fontSize: 15, lineHeight: 1.8 }}>
                  Advanced AI scheduling for modern teams.
                  Automating focus, one calendar at a time.
                </Typography>
                <Stack direction="row" spacing={2.5} component="nav" aria-label="Social links">
                  <Link href="#" aria-label="Visit our website" style={{ color: "var(--text-muted)" }}><Globe size={20} /></Link>
                  <Link href="#" aria-label="Join our community" style={{ color: "var(--text-muted)" }}><Users size={20} /></Link>
                  <Link href="#" aria-label="Check our activity" style={{ color: "var(--text-muted)" }}><Activity size={20} /></Link>
                </Stack>
              </Stack>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography component="h4" sx={{ fontWeight: 800, mb: 3, fontSize: 14, textTransform: "uppercase", letterSpacing: "0.1em" }}>Product</Typography>
              <Stack spacing={2} component="nav">
                <Link href="#" style={{ color: "rgba(15, 23, 42, 0.72)", textDecoration: "none", fontSize: 15 }}>Features</Link>
                <Link href="#" style={{ color: "rgba(15, 23, 42, 0.72)", textDecoration: "none", fontSize: 15 }}>Integrations</Link>
                <Link href="#" style={{ color: "rgba(15, 23, 42, 0.72)", textDecoration: "none", fontSize: 15 }}>Pricing</Link>
                <Link href="#" style={{ color: "rgba(15, 23, 42, 0.72)", textDecoration: "none", fontSize: 15 }}>Security</Link>
              </Stack>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography component="h4" sx={{ fontWeight: 800, mb: 3, fontSize: 14, textTransform: "uppercase", letterSpacing: "0.1em" }}>Company</Typography>
              <Stack spacing={2} component="nav">
                <Link href="#" style={{ color: "rgba(15, 23, 42, 0.72)", textDecoration: "none", fontSize: 15 }}>About</Link>
                <Link href="#" style={{ color: "rgba(15, 23, 42, 0.72)", textDecoration: "none", fontSize: 15 }}>Blog</Link>
                <Link href="#" style={{ color: "rgba(15, 23, 42, 0.72)", textDecoration: "none", fontSize: 15 }}>Careers</Link>
                <Link href="#" style={{ color: "rgba(15, 23, 42, 0.72)", textDecoration: "none", fontSize: 15 }}>Contact</Link>
              </Stack>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography sx={{ fontWeight: 800, mb: 3, fontSize: 14, textTransform: "uppercase", letterSpacing: "0.1em" }}>Subscribe</Typography>
              <Typography sx={{ color: "rgba(15, 23, 42, 0.72)", mb: 3, fontSize: 15 }}>
                Get the latest on AI scheduling and focus optimization.
              </Typography>
              <Box component="form" onSubmit={handleEmailSubmit} noValidate>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                  <TextField
                    inputRef={emailInputRef}
                    type="email"
                    placeholder="name@email.com"
                    value={emailInput}
                    onChange={(e) => {
                      setEmailInput(e.target.value);
                      setEmailError("");
                    }}
                    onBlur={() => {
                      if (emailInput && !isValidEmail(emailInput)) {
                        setEmailError("Invalid email format");
                      }
                    }}
                    disabled={isSubmittingEmail}
                    error={Boolean(emailError)}
                    helperText={emailError}
                    size="small"
                    slotProps={{
                      input: {
                        "aria-label": "Newsletter email subscription",
                        "aria-describedby": emailError ? "email-error" : undefined,
                      }
                    }}
                    sx={{
                      flex: { xs: 1, sm: "unset" },
                      "& .MuiOutlinedInput-root": {
                        borderRadius: "99px",
                        bgcolor: "var(--bg-surface)",
                        px: 3,
                        py: 1.5,
                        border: "1px solid var(--border-subtle)",
                        color: "var(--text-primary)",
                        "&:focus-within": {
                          outline: "2px solid var(--brand-primary)",
                          borderColor: "transparent"
                        }
                      }
                    }}
                  />
                  <Button 
                    type="submit" 
                    disabled={isSubmittingEmail}
                    sx={{ 
                      borderRadius: "99px", 
                      px: 3, 
                      bgcolor: "var(--text-primary)", 
                      color: "var(--bg-base)", 
                      fontWeight: 700,
                      whiteSpace: "nowrap",
                      "&:disabled": {
                        opacity: 0.6
                      }
                    }}
                  >
                    {isSubmittingEmail ? "Joining..." : "Join"}
                  </Button>
                </Stack>
                {emailError && (
                  <Typography id="email-error" sx={{ color: "var(--semantic-danger)", fontSize: 12, mt: 1 }}>
                    {emailError}
                  </Typography>
                )}
                {emailSuccess && (
                  <Alert severity="success" sx={{ mt: 2, borderRadius: 2 }}>
                    Successfully subscribed! Check your inbox.
                  </Alert>
                )}
              </Box>
            </Grid>
          </Grid>
          <Divider sx={{ my: 8, borderColor: "var(--border-subtle)" }} />
          <Stack 
            direction={{ xs: "column", sm: "row" }} 
            justifyContent="space-between" 
            alignItems="center" 
            spacing={2}
            component="nav"
            aria-label="Footer links"
          >
            <Typography sx={{ color: "var(--text-muted)", fontSize: 14 }}>© 2026 GraftAI. All rights reserved.</Typography>
            <Stack direction="row" spacing={4}>
              <Link href="/privacy" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: 14 }}>Privacy</Link>
              <Link href="/terms" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: 14 }}>Terms</Link>
            </Stack>
          </Stack>
        </Container>
      </Box>

      <style jsx global>{`
        @keyframes pulse {
          0% { transform: scale(0.95); opacity: 0.8; }
          50% { transform: scale(1.1); opacity: 1; }
          100% { transform: scale(0.95); opacity: 0.8; }
        }
      `}</style>
      </Box>
      {/* Close position: relative zIndex: 2 wrapper */}
    </Box>
  );
}
