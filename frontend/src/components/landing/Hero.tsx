"use client";

import { Box, Typography, Container, Stack, Button } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { 
  Terminal as TerminalIcon, 
  Cpu, 
  Database, 
  Globe, 
  ChevronRight,
  Activity,
  Zap,
  Code as CodeIcon
} from "lucide-react";
import { useState, useEffect } from "react";
import { CodeSnippetPreview } from "./CodeSnippetPreview";
import { TimeEngineAnimation } from "../ui/TimeEngineAnimation";

const LOG_LINES = [
  { text: "> initializing graftai_engine...", delay: 500, type: "system" },
  { text: "> connecting to redis cluster at 10.0.4.12...", delay: 800, type: "system" },
  { text: "> LOADED: calendar_sync_v4.py", delay: 400, type: "success" },
  { text: "> LOADED: ai_semantic_memory.bin", delay: 600, type: "success" },
  { text: "> indexing vector store user_882 [namespace: personal]", delay: 1000, type: "process" },
  { text: "> found 42 scheduled events in google_calendar", delay: 300, type: "info" },
  { text: "> vectorizing event: 'Technical Interview'", delay: 900, type: "process" },
  { text: "> AI memory updated. Confidence: 0.98", delay: 400, type: "success" },
  { text: "> webhook incoming: hmac_validated=true", delay: 1200, type: "info" },
  { text: "> trigger: distributed_sync_job (PID: 2841)", delay: 300, type: "process" },
  { text: "> graftai is ready. listening on port 8000.", delay: 500, type: "primary" },
];

function TerminalWindow() {
  const [visibleLines, setVisibleLines] = useState<number>(0);

  useEffect(() => {
    if (visibleLines < LOG_LINES.length) {
      const timer = setTimeout(() => {
        setVisibleLines(prev => prev + 1);
      }, LOG_LINES[visibleLines].delay);
      return () => clearTimeout(timer);
    } else {
      setTimeout(() => setVisibleLines(0), 10000);
    }
  }, [visibleLines]);

  return (
    <Box
      sx={{
        width: "100%",
        maxWidth: "540px",
        height: "340px",
        background: "var(--bg-base)",
        border: "1px dashed var(--border-subtle)",
        borderRadius: "0",
        boxShadow: "0 20px 40px rgba(0,0,0,0.8)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        position: "relative",
      }}
    >
      <Box className="scanline" sx={{ opacity: 0.1 }} />

      {/* Header */}
      <Box sx={{ px: 2, py: 1.5, borderBottom: "1px dashed var(--border-subtle)", background: "rgba(255,255,255,0.02)", display: "flex", alignItems: "center", gap: 2 }}>
        <div className="flex gap-1.5">
           <Box sx={{ width: 6, height: 6, background: "var(--text-faint)", opacity: 0.3 }} />
           <Box sx={{ width: 6, height: 6, background: "var(--text-faint)", opacity: 0.6 }} />
           <Box sx={{ width: 6, height: 6, background: "var(--primary)" }} />
        </div>
        <Typography sx={{ fontSize: "9px", color: "var(--primary)", fontFamily: "var(--font-mono)", fontWeight: 900, flex: 1, textTransform: "uppercase", letterSpacing: "0.15em" }}>
          GRAFT_KERNEL_CLI // SHELL_ROOT
        </Typography>
        <div className="flex items-center gap-2">
           <Activity size={10} className="text-[var(--primary)] animate-pulse" />
           <span className="text-[8px] font-black text-[var(--primary)] font-mono">ACTIVE</span>
        </div>
      </Box>

      {/* Content */}
      <Box sx={{ p: 3, flex: 1, overflow: "hidden", display: "flex", flexDirection: "column", background: "rgba(0,0,0,0.4)" }}>
        <AnimatePresence mode="popLayout">
          {LOG_LINES.slice(0, visibleLines).map((line, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.15 }}
              style={{ marginBottom: "6px" }}
            >
              <Typography
                sx={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "10px",
                  fontWeight: 600,
                  lineHeight: 1.2,
                  color: line.type === "success" ? "var(--primary)" : 
                         line.type === "primary" ? "var(--primary)" :
                         line.type === "process" ? "var(--secondary)" :
                         "var(--text-faint)",
                  textShadow: line.type === "primary" ? "0 0 10px rgba(0,255,156,0.2)" : "none",
                  textTransform: "uppercase"
                }}
              >
                {line.text}
              </Typography>
            </motion.div>
          ))}
        </AnimatePresence>
        <div className="flex items-center gap-2 mt-2">
           <span className="text-[var(--primary)] font-mono text-[10px] font-black">{">"}</span>
           <Box sx={{ width: "8px", height: "14px", background: "var(--primary)", animation: "blink 1s infinite" }} />
        </div>
      </Box>

      <style jsx global>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </Box>
  );
}

export function Hero() {
  return (
    <Box
      sx={{
        minHeight: { xs: "auto", md: "100vh" },
        display: "flex",
        alignItems: "center",
        position: "relative",
        background: "var(--bg-base)",
        pt: { xs: 15, md: 0 },
        pb: { xs: 10, md: 0 },
        overflow: "hidden",
      }}
    >
      <TimeEngineAnimation />
      <Box className="scanline" />
      
      <Container maxWidth="xl" sx={{ position: "relative", zIndex: 1, px: { xs: 4, md: 8 } }}>
        <Box
          sx={{
            display: "flex",
            flexDirection: { xs: "column", lg: "row" },
            alignItems: "center",
            gap: { xs: 8, lg: 12 },
          }}
        >
          {/* Left: Value Prop */}
          <Box sx={{ flex: 1.2 }}>
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
            >
              <Stack direction="row" spacing={2} sx={{ mb: 4, alignItems: "center" }}>
                <Box sx={{ px: 2, py: 0.5, background: "var(--primary)", border: "1px dashed var(--primary)", borderRadius: "0" }}>
                  <Typography sx={{ fontSize: "10px", color: "#000", fontWeight: 900, letterSpacing: "0.2em", fontFamily: "var(--font-mono)" }}>
                    BUILD_v3.0.4A_STABLE
                  </Typography>
                </Box>
                <div className="h-[1px] w-12 border-b border-dashed border-[var(--border-subtle)]" />
                <Typography className="telemetry-text">
                  // LATENCY: 0.12MS [OPTIMIZED]
                </Typography>
              </Stack>

              <Typography
                variant="h1"
                sx={{
                  fontSize: { xs: "2.5rem", sm: "3.5rem", md: "5rem" },
                  fontWeight: 900,
                  mb: 4,
                  lineHeight: 0.9,
                  fontFamily: "var(--font-mono)",
                  letterSpacing: "-0.05em",
                  color: "var(--text-primary)",
                  textTransform: "uppercase"
                }}
              >
                PROG_AMMABLE <br />
                <Box component="span" sx={{ color: "var(--primary)", textShadow: "0 0 40px rgba(0,255,156,0.3)" }}>
                  SCHEDULING
                </Box>
              </Typography>

              <Typography
                sx={{
                  color: "var(--text-secondary)",
                  fontSize: { xs: "14px", md: "18px" },
                  lineHeight: 1.6,
                  mb: 6,
                  maxWidth: "600px",
                  fontWeight: 600,
                  fontFamily: "var(--font-mono)",
                  textTransform: "uppercase",
                  letterSpacing: "-0.01em"
                }}
              >
                Zero-trust scheduling infrastructure. Automate availability with vector-backed semantic memory, real-time telemetry, and secure kernel hooks.
              </Typography>

              <Stack direction={{ xs: "column", sm: "row" }} spacing={3} sx={{ mb: 8 }}>
                <Button
                  component={Link}
                  href="/login"
                  sx={{
                    background: "var(--primary)",
                    color: "#000",
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    fontWeight: 900,
                    px: 6,
                    py: 2.5,
                    borderRadius: "0",
                    textTransform: "uppercase",
                    letterSpacing: "0.15em",
                    "&:hover": { background: "#FFF", boxShadow: "0 0 30px rgba(255,255,255,0.4)" }
                  }}
                >
                  <CodeIcon size={18} style={{ marginRight: 12 }} />
                  INIT_SESSION();
                </Button>
                <Button
                  component={Link}
                  href="/developers"
                  sx={{
                    color: "var(--text-primary)",
                    borderColor: "var(--border-subtle)",
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    fontWeight: 900,
                    textTransform: "uppercase",
                    letterSpacing: "0.15em",
                    borderRadius: "0",
                    border: "1px dashed",
                    px: 6,
                    py: 2.5,
                    "&:hover": { borderColor: "var(--primary)", color: "var(--primary)", background: "rgba(0,255,156,0.03)" }
                  }}
                >
                  READ_PROTOCOLS <ChevronRight size={18} />
                </Button>
              </Stack>

              {/* Tech Stack Bar */}
              <Stack direction="row" spacing={6} sx={{ opacity: 0.5 }}>
                {[
                  { label: "POSTGRES_CORE", icon: Database },
                  { label: "VECTOR_DB", icon: Cpu },
                  { label: "AUTH_NODE", icon: Globe },
                ].map((item, idx) => (
                  <Stack key={idx} direction="row" spacing={1.5} alignItems="center">
                    <item.icon size={14} className="text-[var(--text-faint)]" />
                    <Typography className="telemetry-text">{item.label}</Typography>
                  </Stack>
                ))}
              </Stack>
            </motion.div>
          </Box>

          {/* Right: Technical Showcase */}
          <Box sx={{ flex: 0.8, display: "flex", flexDirection: "column", gap: 4, width: "100%" }}>
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <TerminalWindow />
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              <CodeSnippetPreview />
            </motion.div>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}
